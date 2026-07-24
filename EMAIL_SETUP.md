# Email Setup Guide for Kaimur Explorer

## 🚀 Quick Setup (Recommended)

### Option 1: Mailtrap (Free & Easy)

1. **Sign up at Mailtrap**: https://mailtrap.io
2. **Create Inbox**: Click "Create Inbox"
3. **Get SMTP Credentials**:
   - Go to Inbox → Settings → SMTP Settings
   - Copy Username and Password
4. **Update `.env` file**:
   ```
   MAIL_USERNAME=your-actual-mailtrap-username
   MAIL_PASSWORD=your-actual-mailtrap-password
   ```
5. **Restart Backend**: Server restart करें

### Option 2: Gmail SMTP

1. **Enable 2FA** on your Gmail account
2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" → "Other"
   - Enter "Kaimur Explorer"
3. **Update `.env`**:
   ```
   MAIL_USERNAME=your-gmail@gmail.com
   MAIL_PASSWORD=your-16-character-app-password
   ```

## 🧪 Testing Email

1. **Frontend खोलें**: http://localhost:5173
2. **Login click करें**
3. **Email enter करें** (अपना real email)
4. **"Send OTP" click करें**
5. **Email check करें** - OTP मिलेगा!

## 📧 Email Template

OTP emails contain:
- Subject: "Kaimur Explorer OTP Login Code"
- 6-digit OTP code
- Expiration: 5 minutes

## 🔧 Troubleshooting

### Email Not Received?
- Check spam/junk folder
- Verify credentials in `.env`
- Check Mailtrap inbox if using Mailtrap

### Connection Issues?
- Gmail: Make sure app password is correct
- Mailtrap: Verify inbox is active

## 📝 Current Status

- ✅ OTP generation working
- ✅ Database storage working
- ✅ Email sending configured
- ⏳ Needs real credentials for actual email delivery