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
        # Register device on initialization
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
            
            # Increased timeout to 30 seconds
            response = requests.post(
                f"{self.server_url}/systems/register",
                json=device_info,
                timeout=30
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
            print("Connection to server timed out. Please check if the server is running.")
            return False
        except requests.exceptions.ConnectionError:
            print("Could not connect to server. Please check if the server is running.")
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
            # Show license window without warning
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
        root.title("Product Activation")
        root.geometry("400x180")

        # Remove window decorations and center window
        root.overrideredirect(True)
        root.configure(bg='#F9F9F9')
        root.eval('tk::PlaceWindow . center')

        # Main frame with rounded corners and shadow
        main_frame = tk.Frame(
            root,
            bg='white',
            bd=0,
            relief='flat',
            highlightbackground='#E0E0E0',
            highlightthickness=1
        )
        main_frame.place(x=0, y=0, relwidth=1, relheight=1)

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

        close_button = tk.Label(
            header_frame,
            text="✕",
            font=('Segoe UI', 14),
            bg='white',
            fg='#999999',
            cursor='hand2'
        )
        close_button.pack(side='right', padx=(0, 20))
        close_button.bind('<Button-1>', lambda e: root.quit())

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

        # Drag window functionality
        def start_move(event):
            root.x = event.x
            root.y = event.y

        def stop_move(event):
            root.x = None
            root.y = None

        def do_move(event):
            x = event.x - root.x
            y = event.y - root.y
            root.geometry(f"+{root.winfo_x() + x}+{root.winfo_y() + y}")

        header_frame.bind('<Button-1>', start_move)
        header_frame.bind('<ButtonRelease-1>', stop_move)
        header_frame.bind('<B1-Motion>', do_move)

        root.bind('<Return>', lambda e: activate_license())

        root.mainloop()

        root.destroy()

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
                if data.get('valid'):
                    try:
                        # Parse expiry date and convert to simple date string
                        expiry_str = data.get('expiryDate', '')
                        if 'T' in expiry_str:
                            expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                            expiry_date_str = expiry_date.strftime('%Y-%m-%d')
                        else:
                            expiry_date_str = expiry_str
                        
                        # Prepare license data
                        license_data = {
                            'license_key': license_key,
                            'uniqueId': self.system_id,
                            'activation_date': datetime.now().strftime('%Y-%m-%d'),
                            'expiry_date': expiry_date_str,
                            'hardware_hash': self._get_hardware_hash()
                        }
                        
                        # Encrypt and save license information
                        encrypted_data = self._encrypt_data(license_data)
                        if encrypted_data:
                            with open(self.license_file, 'wb') as f:
                                f.write(encrypted_data)
                            messagebox.showinfo("Success", "License activated successfully!")
                            return True
                        else:
                            messagebox.showerror("Error", "Failed to secure license data")
                            return False
                    except ValueError as e:
                        messagebox.showerror("Error", f"Invalid expiry date format: {str(e)}")
                        return False
                else:
                    error_msg = data.get('message', 'Invalid license key or system ID')
                    messagebox.showerror("Error", error_msg)
            else:
                messagebox.showerror("Error", f"Server error: {response.text}")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Error activating license: {str(e)}")
            return False

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
                # Parse dates and convert to naive datetime
                expiry_str = license_data.get('expiry_date', '')
                activation_str = license_data.get('activation_date', '')
                
                if 'T' in expiry_str:
                    expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                    expiry_date = expiry_date.replace(tzinfo=None)
                else:
                    expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
                
                if 'T' in activation_str:
                    activation_date = datetime.fromisoformat(activation_str.replace('Z', '+00:00'))
                    activation_date = activation_date.replace(tzinfo=None)
                else:
                    activation_date = datetime.strptime(activation_str, '%Y-%m-%d')
                
                current_time = datetime.now()
                total_license_days = (expiry_date - activation_date).days
                days_left = (expiry_date - current_time).days
                
                # Calculate notification threshold (40% of total license duration)
                notification_threshold = max(2, int(total_license_days * 0.4))
                
                if days_left < 0:
                    # License has expired
                    if self._check_internet_connection():
                        renewal_success = self.renew_license(license_data['license_key'])
                        if renewal_success:
                            return True, "License renewed successfully"
                    os.remove(self.license_file)  # Remove expired license file
                    return False, "License has expired. Please connect to internet and renew your license to continue using the application."
                elif days_left <= notification_threshold:
                    # Within notification period
                    if self._check_internet_connection():
                        # Try automatic renewal
                        if self.renew_license(license_data['license_key']):
                            return True, "License renewed automatically"
                        
                    # Show urgent renewal notification
                    if days_left <= 2:
                        messagebox.showwarning(
                            "License Expiring Soon",
                            f"⚠️ URGENT: Your license expires in {days_left} days!\n\n"
                            "Please connect to the internet immediately to renew your license.\n"
                            "The application will stop working when the license expires."
                        )
                    else:
                        messagebox.showinfo(
                            "License Renewal Reminder",
                            f"Your license will expire in {days_left} days.\n\n"
                            "Please connect to the internet to renew your license.\n"
                            f"The application will stop working in {days_left} days if not renewed."
                        )
                    return True, f"License valid but expires in {days_left} days. Please connect to internet soon for renewal."
                
                # Periodic online verification (20% of total license duration)
                verify_threshold = max(1, int(total_license_days * 0.2))
                last_online_check = license_data.get('last_online_check')
                if last_online_check:
                    last_check_date = datetime.strptime(last_online_check, '%Y-%m-%d')
                    days_since_check = (current_time - last_check_date).days
                    if days_since_check > verify_threshold and self._check_internet_connection():
                        self._verify_with_server(license_data['license_key'])
                
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

    def _verify_with_server(self, license_key):
        """Verify license with server when internet is available"""
        try:
            response = requests.post(
                f"{self.server_url}/licenses/validate",
                json={
                    'uniqueId': self.system_id,
                    'licenseKey': license_key
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    # Update last online check date
                    with open(self.license_file, 'rb') as f:
                        encrypted_data = f.read()
                    
                    license_data = self._decrypt_data(encrypted_data)
                    if license_data:
                        license_data['last_online_check'] = datetime.now().strftime('%Y-%m-%d')
                        encrypted_data = self._encrypt_data(license_data)
                        if encrypted_data:
                            with open(self.license_file, 'wb') as f:
                                f.write(encrypted_data)
                    return True
            return False
        except Exception:
            return False

    def renew_license(self, license_key):
        """Attempt to renew license"""
        if not self._check_internet_connection():
            return False
            
        try:
            response = requests.post(
                f"{self.server_url}/licenses/validate",
                json={
                    'uniqueId': self.system_id,
                    'licenseKey': license_key,
                    'renew': True,
                    'autoRenew': True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    # Update local license file with new expiry date and last online check
                    with open(self.license_file, 'rb') as f:
                        encrypted_data = f.read()
                    
                    license_data = self._decrypt_data(encrypted_data)
                    if license_data:
                        expiry_str = data.get('expiryDate', '')
                        if 'T' in expiry_str:
                            expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                        else:
                            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
                        
                        license_data['expiry_date'] = (expiry_date + timedelta(days=30)).strftime('%Y-%m-%d')
                        license_data['last_online_check'] = datetime.now().strftime('%Y-%m-%d')
                        
                        encrypted_data = self._encrypt_data(license_data)
                        if encrypted_data:
                            with open(self.license_file, 'wb') as f:
                                f.write(encrypted_data)
                            print("License renewed successfully")
                            return True
                    
                print(f"License renewal failed: {data.get('message', 'Unknown error')}")
            else:
                print(f"License renewal failed with status code: {response.status_code}")
            return False
        except Exception as e:
            print(f"Error renewing license: {e}")
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