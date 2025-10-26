#!/usr/bin/env python3
"""
OMNI Platform Desktop Shortcut Creator
Creates a desktop shortcut with OMNI icon for easy access

Author: OMNI Platform Desktop Integration
Version: 1.0.0
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

class OmniDesktopShortcut:
    """Creates desktop shortcut with OMNI icon"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.desktop = Path(os.path.expanduser("~/Desktop"))
        self.icon_path = self.project_root / "OMNIBOT13" / "omni-brain.ico"
        self.launcher_path = self.project_root / "omni_toggle_launcher_utf8.py"

    def find_icon(self):
        """Find OMNI icon file"""
        # Check primary location
        if self.icon_path.exists():
            return self.icon_path

        # Search for any .ico files in the project
        for ico_file in self.project_root.rglob("*.ico"):
            print(f"✓ Najdena ikona: {ico_file}")
            return ico_file

        return None

    def create_batch_launcher(self):
        """Create a .bat file for easy launching"""
        try:
            batch_content = f'''@echo off
cd /d "{self.project_root}"
echo Starting OMNI Platform...
echo ================================
python omni_toggle_launcher_utf8.py minimal
pause
'''

            batch_path = self.project_root / "launch_omni.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)

            print(f"Batch launcher ustvarjen: {batch_path}")
            return batch_path

        except Exception as e:
            print(f"Napaka pri ustvarjanju batch file-a: {e}")
            return None

    def create_vbs_shortcut(self, target_path, icon_path=None):
        """Create shortcut using VBScript"""
        try:
            # Create VBScript to create shortcut
            vbs_content = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{self.desktop}\\OMNI Platform.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target_path}"
oLink.Arguments = "minimal"
oLink.Description = "OMNI Platform - Professional AI Assistance System"
oLink.WorkingDirectory = "{self.project_root}"
'''

            if icon_path:
                vbs_content += f'oLink.IconLocation = "{icon_path}, 0"\n'

            vbs_content += '''
oLink.Save
WScript.Echo "Shortcut created successfully!"
'''

            # Write VBScript
            vbs_path = self.project_root / "create_shortcut.vbs"
            with open(vbs_path, 'w', encoding='utf-8') as f:
                f.write(vbs_content)

            # Execute VBScript
            result = subprocess.run(['cscript.exe', str(vbs_path)],
                                  capture_output=True, text=True, encoding='utf-8')

            # Clean up VBScript
            try:
                vbs_path.unlink()
            except:
                pass

            if result.returncode == 0:
                print("Bližnjica ustvarjena z VBScript!")
                return True
            else:
                print(f"VBScript napaka: {result.stderr}")
                return False

        except Exception as e:
            print(f"Napaka pri ustvarjanju VBScript bližnjice: {e}")
            return False

    def create_shortcut(self):
        """Create desktop shortcut with OMNI icon"""
        try:
            print("Iscem OMNI ikono...")

            # Find icon
            icon_path = self.find_icon()

            if not icon_path:
                print("Ni najdenih .ico datotek, ustvarjam brez ikone")
                return self.create_shortcut_without_icon()

            print(f"Uporabljam ikono: {icon_path}")

            # Create batch launcher first
            batch_path = self.create_batch_launcher()
            if not batch_path:
                # Fallback to direct Python execution
                target_path = sys.executable
                arguments = f'"{self.launcher_path}" minimal'
            else:
                target_path = str(batch_path)
                arguments = ""

            # Create shortcut using VBScript
            success = self.create_vbs_shortcut(target_path, icon_path)

            if success:
                shortcut_path = self.desktop / "OMNI Platform.lnk"
                print("Bližnjica ustvarjena!")
                print(f"Lokacija: {shortcut_path}")
                print(f"Cilj: {target_path}")
                if arguments:
                    print(f"Argumenti: {arguments}")
                print(f"Ikona: {icon_path}")

                # Copy icon to desktop for better visibility
                try:
                    icon_desktop = self.desktop / "omni-brain.ico"
                    if not icon_desktop.exists():
                        shutil.copy2(icon_path, icon_desktop)
                        print(f"Ikona kopirana na desktop: {icon_desktop}")
                except Exception as e:
                    print(f"Ne morem kopirati ikone na desktop: {e}")

                return True
            else:
                return self.create_shortcut_without_icon()

        except Exception as e:
            print(f"Napaka pri ustvarjanju bližnjice: {e}")
            return self.create_shortcut_without_icon()

    def create_shortcut_without_icon(self):
        """Create shortcut without custom icon"""
        try:
            # Create batch launcher first
            batch_path = self.create_batch_launcher()
            if not batch_path:
                target_path = sys.executable
                arguments = f'"{self.launcher_path}" minimal'
            else:
                target_path = str(batch_path)
                arguments = ""

            # Create shortcut using VBScript
            success = self.create_vbs_shortcut(target_path)

            if success:
                shortcut_path = self.desktop / "OMNI Platform.lnk"
                print("✅ Bližnjica ustvarjena (brez ikone):")
                print(f"Lokacija: {shortcut_path}")
                return True
            else:
                print("Ne morem ustvariti bližnjice")
                return False

        except Exception as e:
            print(f"Napaka pri ustvarjanju bližnjice: {e}")
            return False

def main():
    """Main function to create OMNI desktop shortcut"""
    print("OMNI Platform Desktop Shortcut Creator")
    print("=" * 50)
    print("Ustvarjam bližnjico na namizju z OMNI ikono...")

    creator = OmniDesktopShortcut()

    # Create desktop shortcut
    success = creator.create_shortcut()

    if success:
        print("\nUspesno dokoncano!")
        print("=" * 50)
        print("Naslednji koraki:")
        print("1. Poiscite 'OMNI Platform' na namizju")
        print("2. Dvokliknite za zagon platforme")
        print("3. Platforma se bo zagnala z odstevalnikom casa")
        print("\nIkona prikazuje profesionalni OMNI logotip")
        print("Hitri zagon z minimalnim nacinom")
        print("Avtomatsko preverjanje vseh sistemov")
    else:
        print("\nBližnjica ni bila ustvarjena")
        print("Rocno zaženite: python omni_toggle_launcher_utf8.py minimal")

if __name__ == "__main__":
    main()