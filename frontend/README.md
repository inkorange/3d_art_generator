# Frontend - 3D Painterly Image Generator

Next.js frontend for the 3D Painterly Image Generator.

## Features

- Drag-and-drop image upload
- Real-time job status updates
- Dual mode support (Photo-Realistic & Painterly)
- Parameter controls (layers, style, strength, seed)
- Layer preview and download
- Responsive design with Tailwind CSS
- Dark mode support

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

Frontend will start on `http://localhost:3000`

### 3. Build for Production

```bash
npm run build
npm start
```

## Configuration

Create or edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Usage

1. **Upload Image**: Drag & drop or click to select
2. **Choose Mode**: Photo-Realistic (fast) or Painterly (artistic)
3. **Adjust Parameters**:
   - Number of layers (2-5)
   - For painterly: style, strength, seed
4. **Generate**: Click to start processing
5. **Download**: Get individual layers or all files

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000/api`.

Ensure the backend is running:
```bash
cd ../backend
./run.sh
```

## Components

- `ImageUpload` - Drag-and-drop file upload with preview
- `ParameterControls` - Mode selection and parameter adjustments
- `JobStatus` - Real-time processing status display
- `Results` - Layer preview and download interface

## Technology Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: React hooks
- **API Client**: Custom fetch-based client

## Development

### Project Structure

```
frontend/
├── app/
│   ├── page.tsx          # Main page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── ImageUpload.tsx   # Upload component
│   ├── ParameterControls.tsx  # Parameters
│   ├── JobStatus.tsx     # Status display
│   └── Results.tsx       # Results & download
├── lib/
│   └── api.ts            # API client
├── .env.local            # Environment variables
└── package.json
```

### Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### Connection refused

Ensure backend is running on `http://localhost:8000`

### CORS errors

Backend CORS is configured for `http://localhost:3000` by default

### Upload fails

Check file size (<50MB) and type (image/*)
