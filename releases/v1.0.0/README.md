# Lab Instrument Manager v1.0.0

## Release Information
- **Version:** 1.0.0
- **Release Date:** July 6, 2025
- **Status:** Stable Release

## Files Included
- `main.exe` - Main application executable
- `lab_instruments.db` - Database file with sample data
- `README.md` - This file

## Installation & Usage

### Prerequisites
- Windows 10/11
- No additional software required (standalone executable)

### Installation Steps
1. **Extract Files:** Place both files in the same folder
2. **Run Application:** Double-click `main.exe` to start
3. **Database:** The application will automatically use `lab_instruments.db`

### Default Login Credentials
- **Admin Users:**
  - Username: `admin1` | Password: `admin111`
  - Username: `admin2` | Password: `admin222`
- **Regular Users:**
  - Username: `user1` | Password: `user111`
  - Username: `user2` | Password: `user222`
  - Username: `user3` | Password: `user333`
  - Username: `user4` | Password: `user444`
  - Username: `user5` | Password: `user555`

## Features
- ✅ Instrument Management
- ✅ Maintenance Operations Tracking
- ✅ User Management (Admin only)
- ✅ PDF Report Generation
- ✅ Database Lock Management
- ✅ Professional UI with Dark Theme

## Important Notes
- **Database Location:** The app looks for `lab_instruments.db` in the same folder as `main.exe`
- **Lock File:** A `db.lock` file will be created when the app runs (normal behavior)
- **Permissions:** Ensure the folder has write permissions for the database

## Troubleshooting
- **"Database not found" error:** Ensure `lab_instruments.db` is in the same folder as `main.exe`
- **"Permission denied" error:** Run as administrator or check folder permissions
- **App won't start:** Check Windows Defender/antivirus settings

## Support
For issues or questions, refer to the main project documentation. 