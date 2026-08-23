# QR Code Security & Access Control

## Overview

The Burger Bills menu system implements strict QR code-based access control to prevent unauthorized orders and secure customer transactions.

## How It Works

### 1. QR Code Generation
- One **permanent QR code per table** is generated when the table is created
- The QR code is stored as an image file and can be printed once and reused indefinitely
- Each QR code contains a unique access token and links to the menu for that specific table
- QR codes are never regenerated unless manually triggered through the admin panel

### 2. Access Control Flow
```
Customer scans QR code
    ↓
URL opens with access token: /table/{table_number}/menu/?access={token}
    ↓
System validates the access token against the table's stored token
    ↓
If valid: Creates a secure session with 30-minute expiration (by default)
    ↓
Customer can now access menu, place orders, etc.
    ↓
Session expires after 30 minutes of inactivity
    ↓
Customer must scan QR code again to continue
```

### 3. Session Expiration
- **Default timeout**: 30 minutes of inactivity
- **Configurable per table**: Each table's timeout can be adjusted in the Django admin
- After expiration, customer must scan the QR code again to regain access
- This prevents unauthorized access through bookmarked URLs or accidental sharing

## Security Benefits

✅ **QR Code Only Access**: Menu can only be accessed by scanning the QR code
✅ **No Direct URL Access**: Direct URL visits without valid QR scan are blocked
✅ **Session-Based**: Prevents accidental bookmark sharing between customers
✅ **Inactivity Timeout**: Automatically logs out inactive customers
✅ **Per-Table Isolation**: Customers can only access their assigned table's menu
✅ **No Unauthorized Orders**: Session expiration prevents orders from previous customers

## Configuration

### Adjusting Session Timeout

#### Via Django Admin:
1. Go to `/admin/`
2. Navigate to **Menu > Tables**
3. Click on a table to edit
4. Set **Menu Access Timeout (minutes)** to your desired value
5. Save

Default is 30 minutes. Common options:
- **15 minutes**: Stricter security, good for fast-paced restaurants
- **30 minutes**: Standard, balanced security
- **60 minutes**: Lenient, good for leisurely dining

#### Via Django Shell:
```python
from menu.models import Table

table = Table.objects.get(number=1)
table.menu_access_timeout_minutes = 45  # Set to 45 minutes
table.save()
```

### Regenerating QR Codes

If you need to regenerate a QR code (e.g., if it's damaged):

#### Via Django Admin:
1. Go to `/admin/`
2. Navigate to **Menu > Tables**
3. Click on the table
4. The QR code will be regenerated on save

#### Via Django Shell:
```python
from menu.models import Table
import uuid

table = Table.objects.get(number=1)
table.qr_access_token = uuid.uuid4()  # Generate new token
table.save()  # QR code is automatically regenerated
```

## Error Messages & Handling

### "Access denied. Please scan the QR code at your table."
- User tried to access the menu without a valid session
- **Solution**: Scan the QR code at the table

### "Invalid QR code. Please scan the QR code at your table."
- The QR code was modified or corrupted
- **Solution**: Ask staff for a new QR code

### "Your menu access has expired. Please scan the QR code at your table again."
- The customer's session timed out after X minutes of inactivity
- **Solution**: Scan the QR code again

## Technical Details

### Files Modified
- `menu/models.py`: Added timeout configuration to Table model
- `menu/views.py`: Implemented access token validation and session expiration
- `templates/menu/access_denied.html`: User-friendly error page

### Key Fields
- `Table.qr_access_token`: Unique UUID for QR code validation
- `Table.menu_access_timeout_minutes`: Configurable session timeout
- `Table.qr_code_generated_at`: Timestamp of QR code generation

### Session Variables
- `qr_table_number`: Table number associated with current session
- `qr_access_time`: Timestamp of last activity
- `qr_access_timeout_minutes`: Session timeout in minutes

## Best Practices

1. **Print QR Codes Once**: Print laminated QR codes and place them on tables permanently
2. **Set Appropriate Timeouts**: 
   - 15 min for quick service / fast-casual
   - 30 min for casual dining (default)
   - 60 min for fine dining / leisurely meals
3. **Monitor Sessions**: Check order history if suspicious orders appear
4. **Staff Access**: Staff can still access admin panel without QR codes
5. **Test Regularly**: Periodically test QR codes to ensure they're readable

## Troubleshooting

### QR Code Not Scanning
- Check if the QR code is dirty or damaged
- Try a different smartphone or camera app
- Ensure adequate lighting
- Try regenerating the QR code

### Customer Can't Reorder After Timeout
- This is normal - they must scan the QR code again
- Explain to customer that it's for security
- Staff can help by showing them where the QR code is

### Session Expires Too Quickly
- Increase the timeout in Django admin
- Default is 30 minutes which is reasonable
- Increase if customers take longer than that to order

### Orders from Wrong Table
- Check the order's associated table
- Verify QR codes are properly positioned
- Consider making QR codes more visible/prominent

## Support

For technical support or questions, contact the system administrator.
