# Super Admin Password Viewer Feature

## Overview
Added a password viewer feature that allows Super Admins to view user password hashes and security details.

## What Was Added

### Backend (No Changes Needed)
- The `/api/users/<id>` endpoint already returns user details
- Super Admin needs to use `/api/users/<id>/details` endpoint to get password hash

### Frontend Changes

#### 1. Added Import
```javascript
import { useAuth } from '../context/AuthContext';
```

#### 2. Added State Variables
```javascript
const { user: currentUser } = useAuth();
const [viewingPassword, setViewingPassword] = useState(null);
const [passwordDetails, setPasswordDetails] = useState(null);
```

#### 3. Added Handler Function
```javascript
const handleViewPassword = async (user) => {
  try {
    const { data } = await usersAPI.getById(user.id);
    setPasswordDetails(data);
    setViewingPassword(user.id);
  } catch (error) {
    showError(error?.response?.data?.error || 'Failed to load user details', 'Error');
  }
};
```

#### 4. Added Eye Icon Button (Only for Super Admin)
- Icon appears between Edit and Delete buttons
- Only visible when `currentUser.role === 'super_admin'`
- Clicking opens a modal with password details

#### 5. Added Password Details Modal
Displays:
- Email
- Password Hash (BCrypt) - the encrypted password stored in database
- Reset Token (if active)
- Force Password Change status

## Security Notes

### Important: Passwords Cannot Be Decrypted
- Passwords are hashed using BCrypt
- Hashes are one-way functions - cannot be reversed
- Super Admin can view the hash for security auditing purposes
- Actual plaintext password is never available

### What Super Admin Can See
- **Password Hash**: The encrypted version (e.g., `$2b$12$abc123...`)
- **Reset Tokens**: Active password reset tokens
- **Security Flags**: Force password change status

### What Super Admin CANNOT See
- Actual plaintext password
- Historical passwords
- Unhashed credentials

## Use Cases
1. **Security Auditing**: Verify password hashes are being stored correctly
2. **Troubleshooting**: Check if reset tokens are active
3. **Account Recovery**: Determine if force password change is set
4. **System Administration**: Full visibility into user account security state

## UI/UX
- Eye icon only appears for Super Admin
- Modal displays details in read-only format
- Uses monospace font for technical fields (hashes, tokens)
- Clean, professional design matching existing UI

## Testing
1. Login as Super Admin
2. Navigate to Users page
3. See eye icon next to each user's name
4. Click eye icon to view password details
5. Verify password hash, reset token, and other details display correctly

