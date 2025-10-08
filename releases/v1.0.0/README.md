# Lab Instrument Manager v1.0.0

## Release Information
- **Version:** 1.0.0
- **Release Date:** October 8, 2025
- **Status:** Stable Release (Updated)

## Files Included
- `Lab_Instruments_Manager.exe` - Main application executable
- `lab_instruments.db` - Database file with sample data
- `README.md` - This file

## Installation & Usage

### Prerequisites
- Windows 10/11
- No additional software required (standalone executable)

### Installation Steps
1. **Extract Files:** Place both files in the same folder
2. **Run Application:** Double-click `Lab_Instruments_Manager.exe` to start
3. **Database:** The application will automatically use `lab_instruments.db`

### Default Login Credentials
- **Admin Users:**
  - Username: `admin1` | Password: `Admin11111`
  - Username: `admin2` | Password: `Admin22222`
- **Regular Users:**
  - Username: `user1` | Password: `User11111`
  - Username: `user2` | Password: `User22222`
  - Username: `user3` | Password: `User33333`
  - Username: `user4` | Password: `User44444`
  - Username: `user5` | Password: `User55555`

## Features
- ✅ Instrument Management
- ✅ Maintenance Operations Tracking
- ✅ User Management (Admin only)
- ✅ PDF Report Generation
- ✅ Concurrent Database Access (WAL Mode)
- ✅ Professional UI with Dark Theme
- ✅ Self-Service Profile Editing
- ✅ Enhanced User Permissions
- ✅ Optimized Table Display

## Important Notes
- **Database Location:** The app looks for `lab_instruments.db` in the same folder as `Lab_Instruments_Manager.exe`
- **Concurrent Access:** Multiple users can run the application simultaneously (WAL mode enabled)
- **Permissions:** Ensure the folder has write permissions for the database
- **Network Sharing:** The application works on shared network folders

## Troubleshooting
- **"Database not found" error:** Ensure `lab_instruments.db` is in the same folder as `Lab_Instruments_Manager.exe`
- **"Permission denied" error:** Run as administrator or check folder permissions
- **App won't start:** Check Windows Defender/antivirus settings
- **"Database busy" message:** This is normal when multiple users access simultaneously - wait a moment and try again

## Support
For issues or questions, refer to the main project documentation. 