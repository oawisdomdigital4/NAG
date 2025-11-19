"""
Email Templates for Mailjet
Contains HTML templates for various email types
"""

def welcome_email_template(full_name: str, activation_url: str) -> str:
    """Welcome email template for new users"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .logo-section {{
                background-color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .logo-section img {{
                height: 50px;
                width: auto;
            }}
            .header {{
                background-color: #003a70;
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 0;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border: 1px solid #ddd;
            }}
            .footer {{
                background-color: #f0f0f0;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-radius: 0 0 5px 5px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #e74c3c;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .button:hover {{
                background-color: #c0392b;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-section">
                <img src="https://thenewafricagroup.com/static/TNAG_Black_Logo.png" alt="The New Africa Group Logo">
            </div>
            <div class="header">
                <h1>Welcome to The New Africa Group!</h1>
            </div>
            <div class="content">
                <p>Welcome, {full_name}!</p>
                <p>Thank you for joining our community! We're excited to have you on board.</p>
                <p>To complete your registration and activate your account, please click the button below:</p>
                <p style="text-align: center;">
                    <a href="{activation_url}" class="button">Activate Your Account</a>
                </p>
                <p>If the button doesn't work, you can also copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #0066cc;">{activation_url}</p>
                <p>This link will expire in 24 hours.</p>
                <p>Best regards,<br>The New Africa Group Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 The New Africa Group. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def password_reset_email_template(full_name: str, reset_url: str) -> str:
    """Password reset email template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .logo-section {{
                background-color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .logo-section img {{
                height: 50px;
                width: auto;
            }}
            .header {{
                background-color: #003a70;
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 0;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border: 1px solid #ddd;
            }}
            .footer {{
                background-color: #f0f0f0;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-radius: 0 0 5px 5px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #e74c3c;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .button:hover {{
                background-color: #c0392b;
            }}
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                padding: 10px;
                border-radius: 5px;
                color: #856404;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-section">
                <img src="https://thenewafricagroup.com/static/TNAG_Black_Logo.png" alt="The New Africa Group Logo">
            </div>
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hello {full_name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Your Password</a>
                </p>
                <p>If the button doesn't work, you can also copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #0066cc;">{reset_url}</p>
                <div class="warning">
                    <strong>Security Notice:</strong> This link will expire in 1 hour. If you didn't request a password reset, please ignore this email or contact our support team.
                </div>
                <p>Best regards,<br>The New Africa Group Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 The New Africa Group. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def notification_email_template(full_name: str, notification_title: str, notification_message: str, action_url: str = None) -> str:
    """Generic notification email template"""
    action_button = ""
    if action_url:
        action_button = f'<p style="text-align: center;"><a href="{action_url}" class="button">View More</a></p>'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .logo-section {{
                background-color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .logo-section img {{
                height: 50px;
                width: auto;
            }}
            .header {{
                background-color: #003a70;
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 0;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border: 1px solid #ddd;
            }}
            .footer {{
                background-color: #f0f0f0;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-radius: 0 0 5px 5px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #e74c3c;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .button:hover {{
                background-color: #c0392b;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-section">
                <img src="https://thenewafricagroup.com/static/TNAG_Black_Logo.png" alt="The New Africa Group Logo">
            </div>
            <div class="header">
                <h1>{notification_title}</h1>
            </div>
            <div class="content">
                <p>Hello {full_name},</p>
                <p>{notification_message}</p>
                {action_button}
                <p>Best regards,<br>The New Africa Group Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 The New Africa Group. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def otp_email_template(full_name: str, otp_code: str, expires_in_minutes: int = 10) -> str:
    """OTP verification email template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .logo-section {{
                background-color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .logo-section img {{
                height: 50px;
                width: auto;
            }}
            .header {{
                background-color: #003a70;
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 0;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border: 1px solid #ddd;
            }}
            .footer {{
                background-color: #f0f0f0;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-radius: 0 0 5px 5px;
            }}
            .otp-code {{
                display: inline-block;
                background-color: #f0f0f0;
                border: 2px solid #003a70;
                padding: 20px 30px;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 8px;
                color: #003a70;
                border-radius: 5px;
                text-align: center;
                font-family: 'Courier New', monospace;
                margin: 20px 0;
            }}
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                padding: 10px;
                border-radius: 5px;
                color: #856404;
                margin: 15px 0;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-section">
                <img src="https://thenewafricagroup.com/static/TNAG_Black_Logo.png" alt="The New Africa Group Logo">
            </div>
            <div class="header">
                <h1>Verify Your Account</h1>
            </div>
            <div class="content">
                <p>Hello {full_name},</p>
                <p>Your One-Time Password (OTP) for account verification is:</p>
                <p style="text-align: center;">
                    <div class="otp-code">{otp_code}</div>
                </p>
                <p>Please enter this code on the verification screen to complete your signup.</p>
                <div class="warning">
                    <strong>Important:</strong>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        <li>This code will expire in {expires_in_minutes} minutes</li>
                        <li>Do not share this code with anyone</li>
                        <li>We will never ask you for this code</li>
                    </ul>
                </div>
                <p>If you didn't request this code, please ignore this email.</p>
                <p>Best regards,<br>The New Africa Group Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 The New Africa Group. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
