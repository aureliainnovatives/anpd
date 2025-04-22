import platform
import subprocess
import hashlib
import uuid
import requests
import json
import os
import base64
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import sys
import socket

class LicenseManager:
    def __init__(self):
        self.server_url = "http://localhost:3000/api"
        self.license_file = "license.dat"
        self.system_id = self._generate_system_id()
        self._init_encryption()
        self.renewal_period_minutes = 3  # 3 hours in minutes - change this value to adjust renewal period
        
        # Only try to register device if no valid license exists
        if not os.path.exists(self.license_file):
            self.register_device()
        else:
            try:
                # Check if we have a valid local license
                with open(self.license_file, 'rb') as f:
                    encrypted_data = f.read()
                license_data = self._decrypt_data(encrypted_data)
                if license_data and license_data.get('uniqueId') == self.system_id:
                    # Valid license exists, no need to contact server
                    return
                # If license is invalid or for different system, try to register
                self.register_device()
            except:
                # If any error reading license, try to register
                self.register_device()

    def _init_encryption(self):
        """Initialize encryption key based on hardware information"""
        try:
            # Use hardware info as seed for encryption key
            seed = f"{platform.node()}{platform.processor()}{self._get_windows_uuid()}"
            # Generate a stable key using hardware info
            self.key = hashlib.sha256(seed.encode()).digest()
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            sys.exit(1)

    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """XOR encryption/decryption"""
        return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))

    def _encrypt_data(self, data):
        """Encrypt data with integrity protection"""
        try:
            # Add a checksum before encryption
            data['checksum'] = hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()
            
            # Convert to JSON and encode
            json_data = json.dumps(data).encode()
            
            # XOR encrypt
            encrypted = self._xor_encrypt(json_data, self.key)
            
            # Base64 encode for safe storage
            return base64.b64encode(encrypted)
        except Exception as e:
            print(f"Error encrypting data: {e}")
            return None

    def _decrypt_data(self, encrypted_data):
        """Decrypt data and verify integrity"""
        try:
            # Base64 decode
            decoded = base64.b64decode(encrypted_data)
            
            # XOR decrypt
            decrypted = self._xor_encrypt(decoded, self.key)
            
            # Parse JSON
            decrypted_data = json.loads(decrypted.decode())
            
            # Verify checksum
            stored_checksum = decrypted_data.pop('checksum', None)
            calculated_checksum = hashlib.sha256(
                json.dumps(decrypted_data, sort_keys=True).encode()
            ).hexdigest()
            
            if stored_checksum != calculated_checksum:
                print("License file has been tampered with")
                return None
            return decrypted_data
        except Exception as e:
            print(f"Error decrypting data: {e}")
            return None

    def check_device_exists(self):
        """Check if device is already registered"""
        try:
            response = requests.get(
                f"{self.server_url}/systems/{self.system_id}",
                timeout=30
            )
            return response.status_code == 200
        except:
            return False

    def register_device(self):
        """Register device with the server"""
        # First check if we have a valid local license
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'rb') as f:
                    encrypted_data = f.read()
                license_data = self._decrypt_data(encrypted_data)
                if license_data and license_data.get('uniqueId') == self.system_id:
                    # Valid license exists, no need to register
                    return True
            except:
                pass  # Continue with registration if license check fails
        
        try:
            # Check if device already exists
            if self.check_device_exists():
                print("Device already registered")
                print(f"System ID: {self.system_id}")
                return True

            device_info = {
                'uniqueId': self.system_id,
                'status': 'pending',
                'systemInfo': {
                    'name': platform.node(),
                    'os': platform.system() + ' ' + platform.release(),
                    'processor': platform.processor()
                }
            }
            
            # Increased timeout to 10 seconds
            response = requests.post(
                f"{self.server_url}/systems/register",
                json=device_info,
                timeout=10
            )
            
            if response.status_code == 200:
                print("Device registered successfully")
                print(f"System ID: {self.system_id}")
                return True
            elif response.status_code == 400 and "duplicate key error" in response.text:
                # If we get here, device exists but the GET check failed
                print("Device already registered (duplicate key)")
                print(f"System ID: {self.system_id}")
                return True
            else:
                print(f"Failed to register device. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("Connection to server timed out")
            return False
        except requests.exceptions.ConnectionError:
            print("Could not connect to server")
            return False
        except Exception as e:
            print(f"Error registering device: {e}")
            return False

    def _get_windows_uuid(self):
        """Get Windows UUID using wmic"""
        try:
            uuid_output = subprocess.check_output('wmic csproduct get uuid').decode()
            return uuid_output.split('\n')[1].strip()
        except:
            return str(uuid.getnode())  # Fallback to MAC address

    def _get_cpu_info(self):
        """Get CPU information"""
        try:
            cpu_output = subprocess.check_output('wmic cpu get processorid').decode()
            return cpu_output.split('\n')[1].strip()
        except:
            return platform.processor()

    def _get_disk_info(self):
        """Get disk serial number"""
        try:
            disk_output = subprocess.check_output('wmic diskdrive get serialnumber').decode()
            return disk_output.split('\n')[1].strip()
        except:
            return platform.node()

    def _generate_system_id(self):
        """Generate a unique system ID based on hardware information"""
        try:
            # Collect system information using built-in modules
            system_uuid = self._get_windows_uuid()
            cpu_info = self._get_cpu_info()
            disk_info = self._get_disk_info()
            machine_guid = str(uuid.getnode())
            
            # Combine and hash system information
            system_info = f"{system_uuid}{cpu_info}{disk_info}{machine_guid}"
            return hashlib.sha256(system_info.encode()).hexdigest()
        except Exception as e:
            print(f"Error generating system ID: {e}")
            return None

    def check_license(self):
        """Check if license exists and is valid"""
        is_valid, message = self.verify_license()
        
        if not is_valid:
            # Show expiration message first
            if "expired" in message.lower():
                result = messagebox.showwarning(
                    "License Expired",
                    "Your license has expired. Please contact the administrator to activate the application.",
                    messagebox.Ok | messagebox.Cancel
                )
                if result == messagebox.Ok:
                    # Show license window after user clicks OK
                    if self.show_license_window():
                        # Recheck license after activation
                        is_valid, message = self.verify_license()
                        if not is_valid:
                            messagebox.showerror("Error", "License validation failed after activation")
                            return False
                        return True
                    return False
                else:
                    return False
            else:
                # For other invalid cases, show license window directly
                if self.show_license_window():
                    # Recheck license after activation
                    is_valid, message = self.verify_license()
                    if not is_valid:
                        messagebox.showerror("Error", "License validation failed after activation")
                        return False
                    return True
                return False
        
        if "expires in" in message:
            messagebox.showinfo("License Status", message)
        
        return True

    def show_license_window(self):
        root = tk.Tk()
        
        # Calculate center position before showing window
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 400
        window_height = 180
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Set window properties
        root.title("Product Activation")
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        # root.attributes('-topmost', True)
        root.resizable(False, False)  # Make window non-resizable

        # Main frame with rounded corners and shadow
        main_frame = tk.Frame(
            root,
            bg='white',
            bd=0,
            relief='flat',
            highlightbackground='#E0E0E0',
            highlightthickness=1
        )
        main_frame.pack(fill='both', expand=True, padx=1, pady=1)

        # Header section with icon and title
        header_frame = tk.Frame(main_frame, bg='white')
        header_frame.pack(fill='x', pady=(10, 5))

        icon_label = tk.Label(
            header_frame,
            text="🔑",
            font=('Segoe UI Emoji', 16),
            bg='white',
            fg='#555555'
        )
        icon_label.pack(side='left', padx=(20, 8))

        title_label = tk.Label(
            header_frame,
            text="Product Activation",
            font=('Segoe UI', 12, 'bold'),
            bg='white',
            fg='#333333'
        )
        title_label.pack(side='left')

        # Instruction text
        instruction_label = tk.Label(
            main_frame,
            text="Please enter your license key to activate the product.",
            font=('Segoe UI', 10),
            bg='white',
            fg='#777777'
        )
        instruction_label.pack(pady=(5, 10))

        # License key input box
        entry_frame = tk.Frame(main_frame, bg='white')
        entry_frame.pack(fill='x', padx=20)

        license_entry = tk.Entry(
            entry_frame,
            font=('Segoe UI', 11),
            justify='center',
            relief='solid',
            bd=1,
            fg='#333333',
            bg='#FAFAFA',
            highlightthickness=1,
            highlightcolor='#C0C0C0'
        )
        license_entry.insert(0, "XXXX-XXXX-XXXX-XXXX")
        license_entry.pack(fill='x', ipady=6, padx=(5, 5))
        license_entry.configure(fg='#999999')

        def on_entry_click(event):
            if license_entry.get() == "XXXX-XXXX-XXXX-XXXX":
                license_entry.delete(0, tk.END)
                license_entry.configure(fg='#333333')

        def on_focus_out(event):
            if license_entry.get() == "":
                license_entry.insert(0, "XXXX-XXXX-XXXX-XXXX")
                license_entry.configure(fg='#999999')

        license_entry.bind('<FocusIn>', on_entry_click)
        license_entry.bind('<FocusOut>', on_focus_out)

        # ✅ Define activation_successful at the beginning
        activation_successful = False

        def activate_license():
            nonlocal activation_successful
            license_key = license_entry.get().strip()
            if license_key == "XXXX-XXXX-XXXX-XXXX" or not license_key:
                messagebox.showwarning("Input Required", "Please enter a license key.")
                return

            if self.activate_license(license_key):
                activation_successful = True
                root.quit()

        # Activate button
        activate_button = tk.Button(
            main_frame,
            text="Activate License",
            command=activate_license,
            bg='#808080',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            bd=0
        )
        activate_button.pack(pady=(11, 5), ipadx=120, ipady=10)

        # Button hover effect
        def on_enter(e):
            activate_button['bg'] = '#6F6F6F'

        def on_leave(e):
            activate_button['bg'] = '#808080'

        activate_button.bind('<Enter>', on_enter)
        activate_button.bind('<Leave>', on_leave)

        # Handle window close button
        def on_closing():
            root.quit()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.bind('<Return>', lambda e: activate_license())

        # Focus the entry widget after window is shown
        root.after(100, lambda: license_entry.focus())

        root.mainloop()

        try:
            root.destroy()
        except:
            pass  # Ignore destroy errors

        return activation_successful

    def activate_license(self, license_key):
        """Activate license with the server"""
        try:
            # First check if license is already activated on another system
            check_response = requests.post(
                f"{self.server_url}/licenses/check-activation",
                json={
                    'licenseKey': license_key
                },
                timeout=30
            )
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                if check_data.get('isActivated') and check_data.get('systemId') != self.system_id:
                    messagebox.showerror("Error", "This license key is already activated on another system.")
                    return False

            # Proceed with activation if license is not in use
            response = requests.post(
                f"{self.server_url}/licenses/validate",
                json={
                    'uniqueId': self.system_id,
                    'licenseKey': license_key,
                    'activate': True  # Add flag to indicate this is an activation request
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("Server Response:", data)  # Debug print
                
                if data.get('valid'):
                    try:
                        # Get duration from remainingMinutes in response
                        duration = None
                        if 'remainingMinutes' in data:
                            duration = int(data['remainingMinutes'])
                        elif 'licenseData' in data and 'remainingMinutes' in data['licenseData']:
                            duration = int(data['licenseData']['remainingMinutes'])
                        
                        print(f"Extracted duration: {duration}")  # Debug print
                            
                        if duration is None:
                            messagebox.showerror("Error", "Invalid license: Duration not specified in server response")
                            print("Server response data:", data)  # Debug print full response
                            return False
                            
                        # Validate minimum duration
                        if duration < 5:
                            messagebox.showerror("Error", "Invalid license duration. Minimum duration is 5 minutes.")
                            return False
                            
                        # Get timestamp from expiryDate, or current time if not provided
                        timestamp = None
                        if 'expiryDate' in data:
                            try:
                                expiry_date = datetime.fromisoformat(data['expiryDate'].replace('Z', '+00:00'))
                                # Calculate timestamp as expiry_date minus duration
                                activation_date = expiry_date - timedelta(minutes=duration)
                                timestamp = int(activation_date.timestamp() * 1000)
                            except (ValueError, AttributeError) as e:
                                print(f"Error parsing expiryDate: {e}")
                                timestamp = int(datetime.now().timestamp() * 1000)
                        else:
                            timestamp = int(datetime.now().timestamp() * 1000)
                        
                        # Prepare license data
                        license_data = {
                            'license_key': license_key,
                            'uniqueId': self.system_id,
                            'duration': duration,
                            'timestamp': timestamp,
                            'hardware_hash': self._get_hardware_hash()
                        }
                        
                        print("License data to be saved:", license_data)  # Debug print
                        
                        # Encrypt and save license information
                        encrypted_data = self._encrypt_data(license_data)
                        if encrypted_data:
                            with open(self.license_file, 'wb') as f:
                                f.write(encrypted_data)
                            messagebox.showinfo("Success", f"License activated successfully! Duration: {duration} minutes")
                            return True
                        else:
                            messagebox.showerror("Error", "Failed to secure license data")
                            return False
                    except ValueError as e:
                        messagebox.showerror("Error", f"Invalid license data: {str(e)}")
                        print(f"ValueError during license activation: {e}")  # Debug print
                        return False
                else:
                    error_msg = data.get('message', 'Invalid license key or system ID')
                    messagebox.showerror("Error", error_msg)
            else:
                messagebox.showerror("Error", f"Server error: {response.text}")
                print(f"Server error response: {response.text}")  # Debug print
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Error activating license: {str(e)}")
            print(f"Exception during license activation: {str(e)}")  # Debug print
            return False

    def _print_license_details(self, license_data):
        """Print license details to terminal"""
        try:
            print("\n=== License Details ===")
            print(f"License Key: {license_data.get('license_key', 'N/A')}")
            print(f"System ID: {license_data.get('uniqueId', 'N/A')}")
            
            # Get duration from license data
            duration_minutes = license_data.get('duration', 0)
            print(f"License Duration: {duration_minutes} minutes")
            
            # Calculate activation and expiry dates based on duration
            if 'timestamp' in license_data:
                activation_timestamp = license_data.get('timestamp', 0) / 1000  # Convert from milliseconds to seconds
                activation_date = datetime.fromtimestamp(activation_timestamp)
                expiry_date = activation_date + timedelta(minutes=duration_minutes)
                
                print(f"Activation Date: {activation_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Calculate remaining time
                current_time = datetime.now()
                minutes_left = int((expiry_date - current_time).total_seconds() / 60)
                hours_left = minutes_left // 60
                mins_left = minutes_left % 60
                print(f"Time Remaining: {hours_left} hours and {mins_left} minutes")
            else:
                print("Activation Date: N/A")
                print("Expiry Date: N/A")
                print("Time Remaining: N/A")
            
            print("=====================\n")
        except Exception as e:
            print(f"Error printing license details: {str(e)}")

    def verify_license(self):
        """Verify license and return status with message"""
        try:
            if not os.path.exists(self.license_file):
                return False, "No license file found"
            
            # Read and decrypt license data
            try:
                with open(self.license_file, 'rb') as f:
                    encrypted_data = f.read()
                
                license_data = self._decrypt_data(encrypted_data)
                if not license_data:
                    # If decryption fails, file is tampered
                    os.remove(self.license_file)  # Remove tampered file
                    return False, "License file has been tampered with. Please reactivate your license."
                
                # First check local termination status
                if license_data.get('isTerminated', False):
                    self._handle_termination()
                    return False, "License terminated"
                
                # Validate duration
                duration_minutes = license_data.get('duration', 0)
                if duration_minutes < 5:
                    os.remove(self.license_file)  # Remove invalid license file
                    return False, "Invalid license duration. Minimum duration is 5 minutes."
                
                # Print license details
                self._print_license_details(license_data)
                
            except Exception as e:
                # If any error in reading/decrypting, consider file corrupted
                if os.path.exists(self.license_file):
                    os.remove(self.license_file)
                return False, "License file is corrupted. Please reactivate your license."
            
            # Verify hardware hasn't changed
            if license_data.get('hardware_hash') != self._get_hardware_hash():
                os.remove(self.license_file)  # Remove invalid license file
                return False, "Hardware configuration has changed. Please reactivate your license."

            try:
                # Get duration and calculate expiry
                duration_minutes = license_data.get('duration', 0)
                activation_timestamp = license_data.get('timestamp', 0) / 1000  # Convert from milliseconds to seconds
                activation_date = datetime.fromtimestamp(activation_timestamp)
                expiry_date = activation_date + timedelta(minutes=duration_minutes)
                
                current_time = datetime.now()
                minutes_left = int((expiry_date - current_time).total_seconds() / 60)
                
                if minutes_left < 0:
                    # License has expired
                    os.remove(self.license_file)  # Remove expired license file
                    return False, "License has expired. Please contact administrator to activate the application."
                
                # Check if in renewal period using the renewal_period_minutes variable
                if minutes_left <= self.renewal_period_minutes:
                    return True, f"License valid (Renewal period: {minutes_left} minutes remaining)"
                
                return True, "License valid"
            except ValueError as e:
                return False, f"Invalid date format in license: {str(e)}"
        except Exception as e:
            return False, f"Error verifying license: {str(e)}"

    def _check_internet_connection(self):
        """Check if internet connection is available"""
        try:
            # Try to connect to a reliable server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def _get_hardware_hash(self):
        """Generate a hash of current hardware configuration"""
        hw_info = {
            'uuid': self._get_windows_uuid(),
            'cpu': self._get_cpu_info(),
            'disk': self._get_disk_info(),
            'mac': str(uuid.getnode())
        }
        return hashlib.sha256(json.dumps(hw_info, sort_keys=True).encode()).hexdigest()

    def renew_license(self):
        """Renew license with the server without requiring a license key"""
        try:
            # First check internet connectivity
            if not self._check_internet_connection():
                return False, "No internet connection. Please check your connection and try again."
            
            # Read existing license data
            if not os.path.exists(self.license_file):
                print("Debug: License file not found at:", os.path.abspath(self.license_file))
                return False, "No license file found"
                
            with open(self.license_file, 'rb') as f:
                encrypted_data = f.read()
            
            license_data = self._decrypt_data(encrypted_data)
            if not license_data:
                print("Debug: Failed to decrypt license data")
                return False, "License file has been tampered with"
                
            # Get existing license key and duration
            license_key = license_data.get('license_key')
            duration = license_data.get('duration')
            
            # Check if license is terminated
            if license_data.get('isTerminated', False):
                self._handle_termination()
                return False, "License terminated"
            
            print("Debug: Attempting renewal with:")
            print(f"System ID: {self.system_id}")
            print(f"License Key: {license_key}")
            print(f"Duration: {duration}")
            
            if not license_key or not duration:
                print("Debug: Missing license key or duration in data:", license_data)
                return False, "Invalid license data"
            
            # Request renewal from server
            renewal_data = {
                'uniqueId': self.system_id,
                'licenseKey': license_key,
                'duration': duration
            }
            print("Debug: Sending renewal request:", renewal_data)
            
            response = requests.post(
                f"{self.server_url}/licenses/renew",
                json=renewal_data,
                timeout=30
            )
            
            print("Debug: Server response status:", response.status_code)
            print("Debug: Server response:", response.text)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if license is terminated from server response
                if data.get('isTerminated', False):
                    self._handle_termination()
                    return False, "License terminated"
                
                if data.get('success'):  # Changed from 'valid' to 'success'
                    try:
                        # Get license data from response
                        license_info = data.get('license', {})
                        
                        # Get new duration and remaining minutes
                        new_duration = license_info.get('duration')
                        remaining_minutes = license_info.get('remainingMinutes')
                        
                        print("Debug: New duration from server:", new_duration)
                        print("Debug: Remaining minutes:", remaining_minutes)
                        
                        if not new_duration or not remaining_minutes:
                            return False, "Invalid license: Duration not specified in server response"
                            
                        # Get timestamp from server's startDate
                        timestamp = None
                        if 'startDate' in license_info:
                            try:
                                start_date = datetime.fromisoformat(license_info['startDate'].replace('Z', '+00:00'))
                                timestamp = int(start_date.timestamp() * 1000)
                            except (ValueError, AttributeError) as e:
                                print(f"Error parsing startDate: {e}")
                                timestamp = int(datetime.now().timestamp() * 1000)
                        else:
                            timestamp = int(datetime.now().timestamp() * 1000)
                        
                        # Prepare license data
                        new_license_data = {
                            'license_key': license_key,
                            'uniqueId': self.system_id,
                            'duration': new_duration,
                            'timestamp': timestamp,
                            'hardware_hash': self._get_hardware_hash(),
                            'isTerminated': license_info.get('isTerminated', False)  # Include termination status
                        }
                        
                        # Encrypt and save license information
                        encrypted_data = self._encrypt_data(new_license_data)
                        if encrypted_data:
                            with open(self.license_file, 'wb') as f:
                                f.write(encrypted_data)
                            return True, f"License renewed successfully! Duration: {new_duration} minutes"
                        else:
                            return False, "Failed to secure license data"
                    except ValueError as e:
                        return False, f"Invalid license data: {str(e)}"
                else:
                    error_msg = data.get('message', 'Invalid license key or system ID')
                    # Check if error is due to termination
                    if "terminated" in error_msg.lower():
                        self._handle_termination()
                        return False, "License terminated"
                    return False, error_msg
            else:
                # Check if error response indicates termination
                try:
                    error_data = response.json()
                    if error_data.get('isTerminated', False) or "terminated" in error_data.get('message', '').lower():
                        self._handle_termination()
                        return False, "License terminated"
                except:
                    pass
                return False, f"Server error: {response.text}"
        except Exception as e:
            return False, f"Error renewing license: {str(e)}"

    def _handle_termination(self):
        """Handle license termination by removing license file and closing application"""
        try:
            # Remove the license file if it exists
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
            
            # Show error message
            messagebox.showerror("License Terminated", "Your license has been terminated. Please contact the administrator.")
            
            # Import Qt modules here to avoid circular imports
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QCoreApplication
            
            # Set license termination flag in MainWindow
            app = QApplication.instance()
            if app:
                # Find the MainWindow instance
                for widget in app.topLevelWidgets():
                    if widget.__class__.__name__ == 'MainWindow':
                        widget.license_termination = True
                        break
                app.quit()
            else:
                # Fallback to sys.exit if Qt app is not found
                sys.exit(1)
        except Exception as e:
            print(f"Error handling termination: {str(e)}")