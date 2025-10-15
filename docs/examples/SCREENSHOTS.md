# Screenshot Instructions

To generate screenshots for the design system documentation:

## Automated (Recommended)

1. Install Playwright:
```bash
npm install -D @playwright/test
```

2. Run screenshot script:
```bash
npm run screenshots
```

This will generate:
- `isochrone_d3_light.png` - Isochrone map in light theme
- `isochrone_d3_dark.png` - Isochrone map in dark theme

## Manual

1. Start the dev server:
```bash
cd apps/web
npm run dev
```

2. Navigate to http://localhost:5173/maps/d3-isochrone

3. For light theme:
   - Click theme toggle to ensure light mode
   - Take full-page screenshot
   - Save as `isochrone_d3_light.png`

4. For dark theme:
   - Click theme toggle to switch to dark mode
   - Take full-page screenshot
   - Save as `isochrone_d3_dark.png`

## Screenshot Requirements

- **Resolution:** 1920x1080 minimum
- **Format:** PNG
- **Quality:** High (no compression artifacts)
- **Visible elements:**
  - Header with title
  - Control panel (provider, profile, range, buckets)
  - Map with D3 overlay showing labeled isochrone zones
  - Spot color outline on largest zone
  - Footer with brand compliance note
  - Theme toggle button

## Example Screenshots

Screenshots should demonstrate:
- ✅ No gridlines on map overlay
- ✅ Collision-avoided labels on polygons
- ✅ Spot color (#7823DC light, #AF7DEB dark) on key feature
- ✅ Sequential purple gradient for zones
- ✅ Clean, minimal design
- ✅ No emojis anywhere
