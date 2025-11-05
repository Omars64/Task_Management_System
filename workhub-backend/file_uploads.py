# workhub-backend/file_uploads.py
"""
File Upload Service for Task Attachments
Handles file upload, validation, storage, and retrieval
"""

from flask import Blueprint, request, jsonify, send_file, current_app, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, FileAttachment, Task, User, ProjectMember
from auth import get_current_user
from permissions import Permission
from storage_service import storage_service
import os
import uuid
import mimetypes
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

file_uploads_bp = Blueprint('file_uploads', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z',
    'mp4', 'avi', 'mov', 'mp3', 'wav',
    'csv', 'json', 'xml', 'md', 'log'
}

# Maximum file size: 50 MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB in bytes


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_size(file_obj):
    """Get file size in bytes"""
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)
    return size


def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the extension"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_name = f"{uuid.uuid4().hex}"
    return f"{unique_name}.{ext}" if ext else unique_name


def get_upload_folder():
    """Get or create upload folder path"""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    # Create uploads directory if it doesn't exist
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    return upload_folder


@file_uploads_bp.route('/task/<int:task_id>/upload', methods=['POST'])
@jwt_required()
def upload_file(task_id):
    """
    Upload a file attachment to a task
    
    Form data:
        file: The file to upload
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check if user has permission to add attachments
        # Users can add attachments if they're assigned or created the task
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Permission matrix for attachments:
        # - super_admin/admin: can add to any task
        # - manager/team_lead: can add to tasks in projects they belong to
        # - others: only if assigned or creator
        is_admin_like = (user.role in ('admin', 'super_admin'))
        if not is_admin_like:
            if user.role in ('manager', 'team_lead'):
                if not task.project_id:
                    return jsonify({'error': 'Project not set on task; cannot verify permission'}), 403
                membership = ProjectMember.query.filter_by(project_id=task.project_id, user_id=current_user_id).first()
                if not membership:
                    return jsonify({'error': 'You may only add attachments within your projects'}), 403
            else:
                is_assigned = task.assigned_to == current_user_id
                is_creator = task.created_by == current_user_id
                if not is_assigned and not is_creator:
                    return jsonify({'error': 'You do not have permission to add attachments to this task'}), 403
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Validate file size
        file_size = get_file_size(file)
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)} MB'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(original_filename)
        
        # Save file using storage service (handles both local and cloud)
        file_path = storage_service.save_file(file, unique_filename, subfolder='task_attachments')
        
        # Get file MIME type
        file_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
        
        # Create file attachment record
        attachment = FileAttachment(
            task_id=task_id,
            user_id=current_user_id,
            filename=unique_filename,
            original_filename=original_filename,
            file_size=file_size,
            file_type=file_type,
            file_path=file_path
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        logger.info(f"File uploaded: {original_filename} by user {current_user_id} to task {task_id}")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'attachment': attachment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500


@file_uploads_bp.route('/task/<int:task_id>/attachments', methods=['GET'])
@jwt_required()
def get_task_attachments(task_id):
    """Get all attachments for a task"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Get user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # View permissions similar to upload
        if user.role not in ('admin', 'super_admin'):
            if user.role in ('manager', 'team_lead'):
                if not task.project_id or not ProjectMember.query.filter_by(project_id=task.project_id, user_id=current_user_id).first():
                    return jsonify({'error': 'You may only view attachments within your projects'}), 403
            else:
                if task.assigned_to != current_user_id and task.created_by != current_user_id:
                    return jsonify({'error': 'You do not have permission to view attachments for this task'}), 403
        
        # Get all attachments for this task
        attachments = FileAttachment.query.filter_by(task_id=task_id).order_by(FileAttachment.uploaded_at.desc()).all()
        
        return jsonify([attachment.to_dict() for attachment in attachments]), 200
        
    except Exception as e:
        logger.error(f"Error fetching attachments: {str(e)}")
        return jsonify({'error': str(e)}), 500


@file_uploads_bp.route('/attachment/<int:attachment_id>/download', methods=['GET'])
@jwt_required()
def download_attachment(attachment_id):
    """Download a file attachment"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get attachment
        attachment = FileAttachment.query.get(attachment_id)
        if not attachment:
            return jsonify({'error': 'Attachment not found'}), 404
        
        # Check if task exists
        task = Task.query.get(attachment.task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Get user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Download permission mirrors view
        if user.role not in ('admin', 'super_admin'):
            if user.role in ('manager', 'team_lead'):
                if not task.project_id or not ProjectMember.query.filter_by(project_id=task.project_id, user_id=current_user_id).first():
                    return jsonify({'error': 'You may only download attachments within your projects'}), 403
            else:
                if task.assigned_to != current_user_id and task.created_by != current_user_id:
                    return jsonify({'error': 'You do not have permission to download this file'}), 403
        
        # Check if file is in cloud storage
        if attachment.file_path.startswith('gs://'):
            # Generate signed URL for cloud storage file
            signed_url = storage_service.generate_signed_url(attachment.file_path, expiration_minutes=15)
            if signed_url:
                return redirect(signed_url)
            else:
                return jsonify({'error': 'Failed to generate download URL'}), 500
        else:
            # Local file download
            if not storage_service.file_exists(attachment.file_path):
                return jsonify({'error': 'File not found on server'}), 404
            
            # Send file
            return send_file(
                attachment.file_path,
                as_attachment=True,
                download_name=attachment.original_filename,
                mimetype=attachment.file_type
            )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@file_uploads_bp.route('/attachment/<int:attachment_id>', methods=['DELETE'])
@jwt_required()
def delete_attachment(attachment_id):
    """Delete a file attachment"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get attachment
        attachment = FileAttachment.query.get(attachment_id)
        if not attachment:
            return jsonify({'error': 'Attachment not found'}), 404
        
        # Get user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete: admins/super_admins can delete any; managers/team_leads within project; otherwise only uploader
        if user.role in ('admin', 'super_admin'):
            pass
        elif user.role in ('manager', 'team_lead'):
            task = Task.query.get(attachment.task_id)
            if not task or not task.project_id or not ProjectMember.query.filter_by(project_id=task.project_id, user_id=current_user_id).first():
                return jsonify({'error': 'You may only delete attachments within your projects'}), 403
        else:
            if attachment.user_id != current_user_id:
                return jsonify({'error': 'You do not have permission to delete this file'}), 403
        
        # Delete file from storage (local or cloud)
        try:
            storage_service.delete_file(attachment.file_path)
        except Exception as e:
            logger.error(f"Error deleting file from storage: {str(e)}")
        
        # Delete from database
        db.session.delete(attachment)
        db.session.commit()
        
        logger.info(f"File deleted: {attachment.original_filename} by user {current_user_id}")
        
        return jsonify({'message': 'Attachment deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting attachment: {str(e)}")
        return jsonify({'error': str(e)}), 500


@file_uploads_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_upload_stats():
    """Get upload statistics (admin and super admin only)"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check if user is admin or super_admin
        user = User.query.get(current_user_id)
        if not user or user.role not in ('admin', 'super_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get statistics
        total_files = FileAttachment.query.count()
        total_size = db.session.query(db.func.sum(FileAttachment.file_size)).scalar() or 0
        
        # Get top uploaders
        top_uploaders = db.session.query(
            User.name,
            db.func.count(FileAttachment.id).label('file_count')
        ).join(FileAttachment).group_by(User.id).order_by(db.func.count(FileAttachment.id).desc()).limit(5).all()
        
        return jsonify({
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'top_uploaders': [{'name': name, 'file_count': count} for name, count in top_uploaders]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching upload stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

