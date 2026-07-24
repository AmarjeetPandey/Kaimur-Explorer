#!/usr/bin/env python3
"""
Kaimur Explorer OTP Testing Script
This script demonstrates the OTP login flow
"""

import requests
import json
import time

def test_otp_flow():
    base_url = 'http://127.0.0.1:8000'

    print("🔐 Kaimur Explorer OTP Login Test")
    print("=" * 50)

    # Step 1: Send OTP
    email = input("Enter your email address: ")
    print(f"\n📧 Sending OTP to: {email}")

    send_otp_url = f'{base_url}/api/auth/send-otp'
    response = requests.post(send_otp_url, json={'email': email})

    if response.status_code == 200:
        print("✅ OTP sent successfully!")
        print("📝 Check the backend terminal for the OTP code")
        print("🔍 Look for: '🔑 OTP for [email]: [6-digit-code]'")

        # Step 2: Get OTP from user
        otp = input("\nEnter the 6-digit OTP: ")

        # Step 3: Verify OTP
        verify_url = f'{base_url}/api/auth/verify-otp'
        response = requests.post(verify_url, json={'email': email, 'otp': otp})

        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"🎫 JWT Token: {data['access_token'][:50]}...")
            print(f"👤 User: {data['user']['email']}")
            print(f"👑 Admin: {data['user']['is_admin']}")
        else:
            print("❌ OTP verification failed!")
            print(f"Error: {response.json()}")
    else:
        print("❌ Failed to send OTP!")
        print(f"Error: {response.json()}")

if __name__ == "__main__":
    test_otp_flow()