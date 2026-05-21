# Devil ERP Assets

Place the following files in this folder:

- `logo.png` — Main Devil ERP logo (PNG, transparent background preferred)
- `icon.ico` — Windows EXE icon (convert from logo.png)

## Developer Info
- **Software:** Devil ERP
- **Developed By:** Devil One Pvt Ltd & Nexuzy Lab
- **Lead Developer:** David K. Angel
- **Support:** nexuzylab@gmail.com | devilonepvtltd@gmail.com
- **GitHub:** https://github.com/david0154/DevilERP

## Convert logo.png to icon.ico
```bash
convert logo.png -resize 256x256 assets/icon.ico
# OR use Pillow:
python -c "from PIL import Image; img=Image.open('assets/logo.png'); img.save('assets/icon.ico')"
```
