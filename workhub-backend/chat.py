# workhub-backend/chat.py
"""
Chat API endpoints for direct messaging between users
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from models import db, User, ChatConversation, ChatMessage, MessageReaction
from auth import get_current_user
from notifications import create_notification
from werkzeug.utils import secure_filename
import os
import json

chat_bp = Blueprint('chat', __name__)

# Ephemeral typing and presence states (in-memory with short TTL)
_typing_state = {}  # key: (conversation_id, user_id) -> expire_ts
_presence_last_seen = {}  # key: user_id -> last_ts

def _now_ts():
    return int(datetime.utcnow().timestamp())

def _cleanup_states():
    now = _now_ts()
    # Clean typing entries older than 8 seconds
    to_del = [k for k, exp in _typing_state.items() if exp < now]
    for k in to_del:
        _typing_state.pop(k, None)
    # Presence cleanup not necessary; queried with threshold


def _get_current_user():
    """Get current authenticated user"""
    from auth import get_current_user as _get_user
    return _get_user()


@chat_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """
    Get all users for chat (excluding current user) - accessible to ALL roles
    No role-based restrictions - any authenticated user can see all users for chat
    """
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Return ALL users except current user - no role restrictions
        # All roles (super_admin, admin, manager, team_lead, developer, viewer) can chat with everyone
        users = User.query.filter(
            User.id != current_user.id
        ).all()
        
        users_list = [{
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role
        } for u in users]
        
        # Log for debugging
        print(f"[Chat API] Returning {len(users_list)} users (excluding user {current_user.id})")
        
        return jsonify(users_list), 200
    except Exception as e:
        import traceback
        print(f"[Chat API] Error in get_users: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get all conversations for current user"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Eager load only user relationships, NOT messages (to avoid loading thousands of messages)
        from sqlalchemy.orm import joinedload
        from sqlalchemy import desc
        conversations = ChatConversation.query.options(
            joinedload(ChatConversation.user1),
            joinedload(ChatConversation.user2)
        ).filter(
            (ChatConversation.user1_id == current_user.id) | 
            (ChatConversation.user2_id == current_user.id)
        ).all()
        
        # Convert conversations to dict with efficient message loading
        result = []
        for conv in conversations:
            try:
                # Determine other user safely
                if current_user.id == conv.user1_id:
                    other_user = conv.user2
                else:
                    other_user = conv.user1
                
                # Ensure other_user exists
                if not other_user:
                    print(f"[Chat API] Warning: Conversation {conv.id} has missing user. Skipping.")
                    continue
                
                # Get last message efficiently - limit to recent messages for performance
                last_message = None
                last_message_preview = None
                last_message_time = None
                try:
                    # Use getattr-safe filtering - try to filter by is_deleted, fallback if column doesn't exist
                    try:
                        recent_messages = ChatMessage.query.filter_by(
                            conversation_id=conv.id
                        ).filter(
                            ChatMessage.is_deleted == False
                        ).order_by(desc(ChatMessage.created_at)).limit(50).all()
                    except (AttributeError, Exception) as filter_error:
                        # Column might not exist in database - query without the filter
                        print(f"[Chat API] is_deleted column may not exist, querying without filter: {filter_error}")
                        recent_messages = ChatMessage.query.filter_by(
                            conversation_id=conv.id
                        ).order_by(desc(ChatMessage.created_at)).limit(50).all()
                    
                    # Find first message not deleted for current user
                    for msg in recent_messages:
                        if msg.sender_id == current_user.id and getattr(msg, 'deleted_for_sender', False):
                            continue
                        if msg.recipient_id == current_user.id and getattr(msg, 'deleted_for_recipient', False):
                            continue
                        last_message = msg
                        break
                    
                    # Format last message preview
                    if last_message and last_message.content:
                        try:
                            import json
                            content_data = json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content
                            if isinstance(content_data, dict) and content_data.get('type') == 'file':
                                last_message_preview = f"📎 {content_data.get('name', 'File')}"
                            else:
                                content_str = str(last_message.content)
                                last_message_preview = content_str[:50] + ('...' if len(content_str) > 50 else '')
                        except:
                            try:
                                content_str = str(last_message.content) if last_message.content else ''
                                last_message_preview = content_str[:50] + ('...' if len(content_str) > 50 else '')
                            except:
                                last_message_preview = None
                        
                        if last_message.created_at:
                            last_message_time = last_message.created_at.isoformat()
                except Exception as msg_error:
                    print(f"[Chat API] Error loading messages for conversation {conv.id}: {msg_error}")
                    # Continue without last message
                
                # Get unread count efficiently
                unread_count = 0
                try:
                    unread_count = ChatMessage.query.filter_by(
                        conversation_id=conv.id,
                        recipient_id=current_user.id,
                        is_read=False
                    ).count()
                except Exception as unread_error:
                    print(f"[Chat API] Error counting unread for conversation {conv.id}: {unread_error}")
                    unread_count = 0
                
                # Build result - ensure all fields are safe
                conv_dict = {
                    'id': conv.id,
                    'other_user': {
                        'id': other_user.id,
                        'name': other_user.name if other_user.name else 'Unknown',
                        'email': other_user.email if other_user.email else ''
                    },
                    'status': conv.status or 'pending',
                    'requested_by': conv.requested_by,
                    'requested_at': conv.requested_at.isoformat() if conv.requested_at else None,
                    'accepted_at': conv.accepted_at.isoformat() if conv.accepted_at else None,
                    'created_at': conv.created_at.isoformat() if conv.created_at else None,
                    'unread_count': unread_count,
                    'last_message': last_message_preview,
                    'last_message_time': last_message_time
                }
                result.append(conv_dict)
            except Exception as conv_error:
                import traceback
                print(f"[Chat API] Error converting conversation {conv.id} to dict: {str(conv_error)}")
                traceback.print_exc()
                # Try to return at least basic info
                try:
                    other_user = conv.user2 if current_user.id == conv.user1_id else conv.user1
                    if other_user:
                        result.append({
                            'id': conv.id,
                            'other_user': {
                                'id': other_user.id,
                                'name': other_user.name or 'Unknown',
                                'email': other_user.email or ''
                            },
                            'status': conv.status or 'pending',
                            'requested_by': conv.requested_by,
                            'requested_at': conv.requested_at.isoformat() if conv.requested_at else None,
                            'accepted_at': conv.accepted_at.isoformat() if conv.accepted_at else None,
                            'created_at': conv.created_at.isoformat() if conv.created_at else None,
                            'unread_count': 0,
                            'last_message': None,
                            'last_message_time': None
                        })
                except:
                    print(f"[Chat API] Failed to create fallback dict for conversation {conv.id}")
                    continue
        
        return jsonify(result), 200
    except Exception as e:
        import traceback
        print(f"[Chat API] Error in get_conversations: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/request', methods=['POST'])
@jwt_required()
def request_chat():
    """
    Request a chat with another user - accessible to ALL roles
    Any authenticated user can initiate chat with any other user
    """
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        payload = request.get_json(silent=True) or {}
        other_user_id = payload.get('user_id')
        
        if not other_user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Convert to integer if it's a string
        try:
            other_user_id = int(other_user_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid user_id format'}), 400
        
        if other_user_id == current_user.id:
            return jsonify({'error': 'Cannot chat with yourself'}), 400
        
        other_user = User.query.get(other_user_id)
        if not other_user:
            return jsonify({'error': 'User not found'}), 404
        
        # No restrictions - all users can chat with each other
        # Check if conversation already exists
        existing = ChatConversation.query.filter(
            ((ChatConversation.user1_id == current_user.id) & (ChatConversation.user2_id == other_user_id)) |
            ((ChatConversation.user1_id == other_user_id) & (ChatConversation.user2_id == current_user.id))
        ).first()
        
        if existing:
            # Eager load user relationships before calling to_dict
            from sqlalchemy.orm import joinedload
            existing = ChatConversation.query.options(
                joinedload(ChatConversation.user1),
                joinedload(ChatConversation.user2)
            ).get(existing.id)
            
            if existing.status == 'accepted':
                return jsonify({'message': 'Conversation already exists', 'conversation': existing.to_dict(current_user.id)}), 200
            elif existing.status == 'pending':
                # Return the existing pending conversation instead of error
                return jsonify({'message': 'Chat request already pending', 'conversation': existing.to_dict(current_user.id)}), 200
            elif existing.status == 'rejected':
                # Allow creating a new request after rejection - delete the old rejected conversation
                db.session.delete(existing)
                db.session.flush()
                # Continue to create new conversation below
        
        # Create new conversation request
        # Ensure user1_id < user2_id for consistency
        user1_id, user2_id = sorted([current_user.id, other_user_id])
        
        print(f"[Chat API] Creating chat request: user1_id={user1_id}, user2_id={user2_id}, requested_by={current_user.id}")
        
        conversation = ChatConversation(
            user1_id=user1_id,
            user2_id=user2_id,
            status='pending',
            requested_by=current_user.id
        )
        
        db.session.add(conversation)
        try:
            db.session.commit()
            print(f"[Chat API] Chat conversation created successfully with ID: {conversation.id}")
        except Exception as commit_error:
            db.session.rollback()
            print(f"[Chat API] Error committing conversation: {commit_error}")
            raise
        
        # Eager load user relationships before calling to_dict
        from sqlalchemy.orm import joinedload
        conversation_id = conversation.id
        conversation = ChatConversation.query.options(
            joinedload(ChatConversation.user1),
            joinedload(ChatConversation.user2)
        ).get(conversation_id)
        
        if not conversation:
            print(f"[Chat API] ERROR: Conversation {conversation_id} not found after creation!")
            return jsonify({'error': 'Failed to create conversation'}), 500
        
        # Create notification for the other user
        try:
            from notifications import create_notification
            create_notification(
                user_id=other_user_id,
                title='New Chat Request',
                message=f'{current_user.name} wants to start a chat with you',
                notif_type='chat_request',
                related_conversation_id=conversation.id
            )
            print(f"[Chat API] Notification created for user {other_user_id}")
        except Exception as notif_error:
            print(f"[Chat API] Warning: Failed to create notification: {notif_error}")
            # Don't fail the request if notification fails
        
        try:
            conv_dict = conversation.to_dict(current_user.id)
            print(f"[Chat API] Successfully converted conversation to dict")
            return jsonify({'message': 'Chat request sent', 'conversation': conv_dict}), 201
        except Exception as dict_error:
            print(f"[Chat API] Error converting conversation to dict: {dict_error}")
            import traceback
            traceback.print_exc()
            # Return basic response even if to_dict fails
            return jsonify({
                'message': 'Chat request sent',
                'conversation': {
                    'id': conversation.id,
                    'status': conversation.status,
                    'other_user': {
                        'id': other_user.id,
                        'name': other_user.name,
                        'email': other_user.email
                    }
                }
            }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        import traceback
        print(f"[Chat API] SQLAlchemy error in request_chat: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"[Chat API] Error in request_chat: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/accept', methods=['POST'])
@jwt_required()
def accept_chat(conversation_id):
    """
    Accept a chat request - accessible to ALL roles
    Any authenticated user can accept chat requests from any other user
    """
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verify user is part of conversation
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Prevent user from accepting their own request
        if conversation.requested_by == current_user.id:
            return jsonify({'error': 'You cannot accept your own chat request'}), 400
        
        if conversation.status != 'pending':
            return jsonify({'error': 'Conversation is not pending'}), 400
        
        conversation.status = 'accepted'
        conversation.accepted_at = datetime.utcnow()
        db.session.commit()
        
        # Eager load user relationships before calling to_dict
        from sqlalchemy.orm import joinedload
        conversation = ChatConversation.query.options(
            joinedload(ChatConversation.user1),
            joinedload(ChatConversation.user2)
        ).get(conversation.id)
        
        # Notify the requester
        requester_id = conversation.user2_id if conversation.user1_id == current_user.id else conversation.user1_id
        requester = User.query.get(requester_id)
        if requester:
            from notifications import create_notification
            create_notification(
                user_id=requester_id,
                title='Chat Request Accepted',
                message=f'{current_user.name} accepted your chat request',
                notif_type='chat_accepted',
                related_conversation_id=conversation.id
            )
        
        return jsonify({'message': 'Chat request accepted', 'conversation': conversation.to_dict(current_user.id)}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/reject', methods=['POST'])
@jwt_required()
def reject_chat(conversation_id):
    """Reject a chat request"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verify user is part of conversation
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        conversation.status = 'rejected'
        db.session.commit()
        
        return jsonify({'message': 'Chat request rejected'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conversation_id):
    """Get messages in a conversation - WhatsApp-like simple messaging"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verify user is part of conversation
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # If conversation is not accepted, return empty array instead of error
        if conversation.status != 'accepted':
            return jsonify([]), 200
        
        # Eager load messages with all relationships to prevent lazy loading errors
        # This is the key: load all relationships upfront like the model's to_dict() expects
        from sqlalchemy.orm import joinedload, selectinload
        messages = ChatMessage.query.options(
            joinedload(ChatMessage.sender),
            joinedload(ChatMessage.recipient),
            joinedload(ChatMessage.reply_to).joinedload(ChatMessage.sender),
            selectinload(ChatMessage.reactions).joinedload(MessageReaction.user)
        ).filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # Filter out messages that are hidden for current user
        filtered_messages = []
        for msg in messages:
            # Skip if deleted for this specific user (use getattr for backward compat)
            if msg.sender_id == current_user.id and getattr(msg, 'deleted_for_sender', False):
                continue
            if msg.recipient_id == current_user.id and getattr(msg, 'deleted_for_recipient', False):
                continue
            if getattr(msg, 'is_deleted', False):
                continue
            
            # Use the model's to_dict() method - it works when relationships are loaded
            try:
                filtered_messages.append(msg.to_dict())
            except Exception as e:
                # If to_dict() fails, skip this message but log the error
                print(f"[Chat API] Error calling to_dict() for message {msg.id}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        return jsonify(filtered_messages), 200
    except Exception as e:
        import traceback
        print(f"[Chat API] Error in get_messages: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    """Send a message in a conversation"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verify user is part of conversation
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if conversation.status != 'accepted':
            return jsonify({'error': 'Conversation not accepted'}), 400
        
        payload = request.get_json(silent=True) or {}
        content = payload.get('content', '').strip()
        reply_to_id = payload.get('reply_to_id')  # Optional: ID of message being replied to
        
        if not content:
            return jsonify({'error': 'Message content is required'}), 400
        
        # Validate reply_to_id if provided
        if reply_to_id:
            reply_message = ChatMessage.query.get(reply_to_id)
            if not reply_message or reply_message.conversation_id != conversation_id:
                return jsonify({'error': 'Invalid reply message'}), 400
        
        # Determine recipient
        recipient_id = conversation.user2_id if conversation.user1_id == current_user.id else conversation.user1_id
        
        message = ChatMessage(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content,
            reply_to_id=reply_to_id,
            delivery_status='sent'
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Eager load relationships before calling to_dict() - like the previous working version
        from sqlalchemy.orm import joinedload, selectinload
        message_id = message.id
        message = ChatMessage.query.options(
            joinedload(ChatMessage.sender),
            joinedload(ChatMessage.recipient),
            joinedload(ChatMessage.reply_to).joinedload(ChatMessage.sender),
            selectinload(ChatMessage.reactions).joinedload(MessageReaction.user)
        ).get(message_id)
        
        # Create notification for recipient
        from notifications import create_notification
        create_notification(
            user_id=recipient_id,
            title='New Message',
            message=f'{current_user.name}: {content[:50]}...' if len(content) > 50 else f'{current_user.name}: {content}',
            notif_type='chat_message',
            related_conversation_id=conversation_id
        )
        
        # Use the model's to_dict() method - simple and clean like the previous version
        return jsonify({'message': 'Message sent', 'chat_message': message.to_dict()}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/attachments', methods=['POST'])
@jwt_required()
def upload_chat_attachment(conversation_id):
    """Upload a file attachment and create a chat message with a file payload (<=100 MB)."""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verify membership
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        if conversation.status != 'accepted':
            return jsonify({'error': 'Conversation not accepted'}), 400
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        f = request.files['file']
        if f.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate size (50 MB)
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        if size > 50 * 1024 * 1024:
            return jsonify({'error': 'File exceeds 50 MB limit'}), 400
        
        upload_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        original = secure_filename(f.filename)
        unique = f"chat_{conversation_id}_{current_user.id}_{int(datetime.utcnow().timestamp())}_{original}"
        path = os.path.join(upload_folder, unique)
        f.save(path)
        
        recipient_id = conversation.user2_id if conversation.user1_id == current_user.id else conversation.user1_id
        payload = {
            'type': 'file',
            'name': original,
            'size': size,
            'message': 'File attachment',
            'file_key': unique
        }
        message = ChatMessage(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=json.dumps(payload),
            delivery_status='sent'
        )
        db.session.add(message)
        db.session.commit()
        
        # Notify recipient
        try:
            create_notification(
                user_id=recipient_id,
                title='New Attachment',
                message=f'{current_user.name} sent a file: {original}',
                notif_type='chat_message',
                related_conversation_id=conversation_id
            )
        except Exception:
            pass
        
        return jsonify({'message': 'Attachment sent', 'chat_message': message.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/attachments/<int:message_id>', methods=['GET'])
@jwt_required()
def download_chat_attachment(message_id):
    """Download a chat attachment associated with a message id."""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Authorization: only participants
        conversation = ChatConversation.query.get(message.conversation_id)
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        try:
            data = json.loads(message.content or '{}')
        except Exception:
            data = {}
        file_key = data.get('file_key')
        name = data.get('name', 'download')
        if not file_key:
            return jsonify({'error': 'No attachment found'}), 404
        upload_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
        path = os.path.join(upload_folder, file_key)
        if not os.path.exists(path):
            return jsonify({'error': 'File not found'}), 404
        from flask import send_file
        return send_file(path, as_attachment=True, download_name=name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/typing', methods=['POST'])
@jwt_required()
def set_typing(conversation_id):
    """Set typing state for current user in a conversation (ephemeral)."""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        payload = request.get_json(silent=True) or {}
        is_typing = bool(payload.get('typing', False))
        _cleanup_states()
        if is_typing:
            _typing_state[(conversation_id, current_user.id)] = _now_ts() + 8  # expire in 8s
        else:
            _typing_state.pop((conversation_id, current_user.id), None)
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/typing', methods=['GET'])
@jwt_required()
def get_typing(conversation_id):
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        _cleanup_states()
        other_id = conversation.user2_id if conversation.user1_id == current_user.id else conversation.user1_id
        typing = ((conversation_id, other_id) in _typing_state)
        return jsonify({'typing': typing}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/presence/heartbeat', methods=['POST'])
@jwt_required()
def presence_heartbeat():
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        _presence_last_seen[current_user.id] = _now_ts()
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/presence/<int:user_id>', methods=['GET'])
@jwt_required()
def presence_status(user_id):
    try:
        # anyone logged in can query presence; presence is non-sensitive
        now = _now_ts()
        last = _presence_last_seen.get(user_id, 0)
        return jsonify({'online': (now - last) <= 60, 'last_seen': last}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<int:message_id>/delivered', methods=['PUT'])
@jwt_required()
def mark_delivered(message_id):
    """Mark message as delivered (double gray tick)"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        if message.recipient_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        message.delivery_status = 'delivered'
        db.session.commit()
        
        return jsonify({'message': 'Message marked as delivered'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<int:message_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(message_id):
    """Mark message as read (double colored tick)"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        if message.recipient_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        message.is_read = True
        message.delivery_status = 'read'
        message.read_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Message marked as read'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/read', methods=['POST'])
@jwt_required()
def mark_conversation_read(conversation_id):
    """Mark all messages in a conversation as read"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verify user is part of conversation
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Mark all unread messages as read
        ChatMessage.query.filter_by(
            conversation_id=conversation_id,
            recipient_id=current_user.id,
            is_read=False
        ).update({
            'is_read': True,
            'delivery_status': 'read',
            'read_at': datetime.utcnow()
        })
        
        db.session.commit()
        
        return jsonify({'message': 'Messages marked as read'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<int:message_id>', methods=['PUT'])
@jwt_required()
def edit_message(message_id):
    """Edit a message (within 30 minutes of creation)"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Only sender can edit their own message
        if message.sender_id != current_user.id:
            return jsonify({'error': 'You can only edit your own messages'}), 403
        
        # Check if message was deleted (use getattr for backward compat)
        if getattr(message, 'is_deleted', False):
            return jsonify({'error': 'Cannot edit deleted message'}), 400
        
        # Check 30-minute time limit
        time_diff = datetime.utcnow() - message.created_at
        if time_diff.total_seconds() > 1800:  # 30 minutes = 1800 seconds
            return jsonify({'error': 'Messages can only be edited within 30 minutes'}), 400
        
        payload = request.get_json(silent=True) or {}
        new_content = payload.get('content', '').strip()
        
        if not new_content:
            return jsonify({'error': 'Message content is required'}), 400
        
        message.content = new_content
        message.updated_at = datetime.utcnow()
        message.is_edited = True
        db.session.commit()
        
        return jsonify({'message': 'Message updated successfully', 'chat_message': message.to_dict()}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<int:message_id>/delete-for-me', methods=['DELETE'])
@jwt_required()
def delete_message_for_me(message_id):
    """Delete/hide a message for current user only"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # User must be sender or recipient
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Mark as deleted for this user (use setattr for backward compat)
        if message.sender_id == current_user.id:
            if hasattr(message, 'deleted_for_sender'):
                message.deleted_for_sender = True
        else:
            if hasattr(message, 'deleted_for_recipient'):
                message.deleted_for_recipient = True
        
        db.session.commit()
        
        return jsonify({'message': 'Message deleted for you'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<int:message_id>/delete-for-everyone', methods=['DELETE'])
@jwt_required()
def delete_message_for_everyone(message_id):
    """Delete a message for everyone (within 30 minutes of creation, sender only)"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Only sender can delete for everyone
        if message.sender_id != current_user.id:
            return jsonify({'error': 'You can only delete your own messages for everyone'}), 403
        
        # Check if already deleted (use getattr for backward compat)
        if getattr(message, 'is_deleted', False):
            return jsonify({'error': 'Message already deleted'}), 400
        
        # Check 30-minute time limit
        time_diff = datetime.utcnow() - message.created_at
        if time_diff.total_seconds() > 1800:  # 30 minutes = 1800 seconds
            return jsonify({'error': 'Messages can only be deleted for everyone within 30 minutes'}), 400
        
        # Set is_deleted if column exists (backward compat)
        if hasattr(message, 'is_deleted'):
            message.is_deleted = True
        message.content = 'This message was deleted'
        db.session.commit()
        
        return jsonify({'message': 'Message deleted for everyone'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<int:message_id>/reactions', methods=['POST'])
@jwt_required()
def add_reaction(message_id):
    """Add an emoji reaction to a message"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Verify user is part of the conversation
        conversation = ChatConversation.query.get(message.conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        payload = request.get_json(silent=True) or {}
        emoji = payload.get('emoji', '').strip()
        
        if not emoji:
            return jsonify({'error': 'Emoji is required'}), 400
        
        # Ensure emoji is properly encoded as UTF-8 string
        # Remove any null bytes or invalid characters
        emoji = emoji.replace('\0', '').strip()
        
        # Validate it's a valid Unicode string (not corrupted)
        try:
            # Try to encode/decode to validate UTF-8
            emoji_bytes = emoji.encode('utf-8')
            emoji = emoji_bytes.decode('utf-8')
            # Skip if it contains replacement characters (corrupted) or is empty
            if not emoji or '??' in emoji or '\ufffd' in emoji:  # \ufffd is the Unicode replacement character
                return jsonify({'error': 'Invalid emoji format'}), 400
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            return jsonify({'error': 'Invalid emoji encoding'}), 400
        
        # Check if reaction already exists (unique constraint will prevent duplicates)
        existing = MessageReaction.query.filter_by(
            message_id=message_id,
            user_id=current_user.id,
            emoji=emoji
        ).first()
        
        if existing:
            # Toggle off - remove the reaction
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'message': 'Reaction removed', 'removed': True}), 200
        
        # Add new reaction
        reaction = MessageReaction(
            message_id=message_id,
            user_id=current_user.id,
            emoji=emoji
        )
        
        db.session.add(reaction)
        db.session.commit()
        
        return jsonify({'message': 'Reaction added', 'reaction': reaction.to_dict()}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<int:message_id>/reactions/<int:reaction_id>', methods=['DELETE'])
@jwt_required()
def remove_reaction(message_id, reaction_id):
    """Remove a specific reaction from a message"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        reaction = MessageReaction.query.get(reaction_id)
        if not reaction:
            return jsonify({'error': 'Reaction not found'}), 404
        
        if reaction.message_id != message_id:
            return jsonify({'error': 'Reaction does not belong to this message'}), 400
        
        # Only the user who added the reaction can remove it
        if reaction.user_id != current_user.id:
            return jsonify({'error': 'You can only remove your own reactions'}), 403
        
        db.session.delete(reaction)
        db.session.commit()
        
        return jsonify({'message': 'Reaction removed'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
