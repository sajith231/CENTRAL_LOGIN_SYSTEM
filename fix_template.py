
# Script to fix the broken template tag in mobileapp_billing.html
file_path = "c:\\Users\\thoma\\Desktop\\IMC\\CENTRAL_LOGIN_SYSTEM\\MobileApp\\templates\\mobileapp_billing.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern: ...disabled{%
# ...                            endif %}

# Replace
if 'disabled{%' in content:
    print("Found disabled{% tag!")
    new_content = content.replace("disabled{%\n                            endif %}", "disabled{% endif %}")
    # Also handle Windows line endings if any
    new_content = new_content.replace("disabled{%\r\n                            endif %}", "disabled{% endif %}")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Fixed file.")
else:
    print("Could not find disabled{% tag.")

