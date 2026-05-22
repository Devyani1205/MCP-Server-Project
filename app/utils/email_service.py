import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings

def send_otp_email(to_email: str, otp: str):
    """
    Sends a branded HTML OTP code to the user's email using SMTP.
    """
    print(f"\n[SMTP] --- Starting Email Flow ---")
    print(f"[SMTP] Target: {to_email}")
    
    if not settings.EMAIL_USER or not settings.EMAIL_PASS:
        print(f"[SMTP] ERROR: EMAIL_USER or EMAIL_PASS not set.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"MindsNXT Auth <{settings.EMAIL_USER}>"
        msg['To'] = to_email
        msg['Subject'] = f"{otp} is your verification code"

        # HTML Template
        html = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    <div style="background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); padding: 30px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">MindsNXT Authentication</h1>
                    </div>
                    <div style="padding: 40px; text-align: center; color: #374151;">
                        <h2 style="font-size: 20px; margin-bottom: 20px;">Verify Your Identity</h2>
                        <p style="font-size: 16px; line-height: 1.6; color: #6b7280;">
                            Please use the following One-Time Password (OTP) to complete your request. This code is valid for 10 minutes.
                        </p>
                        <div style="background-color: #f3f4f6; border-radius: 8px; padding: 20px; margin: 30px 0; display: inline-block; min-width: 200px;">
                            <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #111827;">{otp}</span>
                        </div>
                        <p style="font-size: 14px; color: #9ca3af; margin-top: 20px;">
                            <strong>Warning:</strong> For your security, do not share this code with anyone. 
                            If you didn't request this, please ignore this email.
                        </p>
                    </div>
                    <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                        <p style="font-size: 12px; color: #9ca3af; margin: 0;">&copy; 2026 MindsNXT Diagnostic Platform. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        part1 = MIMEText(f"Your OTP is {otp}. It expires in 10 minutes.", 'plain')
        part2 = MIMEText(html, 'html')

        msg.attach(part1)
        msg.attach(part2)

        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=15)
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        
        print(f"[SMTP] Email SENT SUCCESSFULLY to {to_email}.")
        return True
        
    except Exception as e:
        print(f"[SMTP] ERROR: {e}")
        return False
