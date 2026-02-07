# cliqueAI Frontend

Modern Vue.js 3 frontend application for cliqueAI - a platform for connecting people in focused 48-hour pods.

## Features

- 🔐 User authentication (register, login, logout)
- 🎯 Multi-step onboarding flow
- 🔍 Semantic matching system
- 💬 Real-time messaging interface
- 📱 Fully responsive design
- ⚡ Built with Vue 3, Pinia, and Tailwind CSS

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **Vue Router 4** - Official router for Vue.js
- **Pinia** - State management for Vue
- **Axios** - HTTP client for API requests
- **Tailwind CSS** - Utility-first CSS framework
- **@vueuse/core** - Collection of Vue composition utilities
- **Vite** - Next generation frontend tooling

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── main.js            # Vue app initialization
│   ├── App.vue             # Root component
│   ├── router/
│   │   └── index.js        # Vue Router configuration
│   ├── stores/
│   │   ├── auth.js         # Authentication store
│   │   └── pod.js          # Pod state store
│   ├── services/
│   │   ├── api.js          # Axios instance with interceptors
│   │   └── auth.js         # Auth service methods
│   ├── components/
│   │   ├── common/         # Reusable components
│   │   ├── onboarding/     # Onboarding components
│   │   ├── matching/       # Matching components
│   │   └── messaging/      # Messaging components
│   ├── views/              # Page components
│   └── assets/
│       └── styles/         # Global styles
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

## Setup Instructions

### Prerequisites

- Node.js 16+ and npm/yarn/pnpm
- Backend API running on `http://localhost:5000` (or configure via environment variables)

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables:**
   Edit `.env` and set:
   ```
   VITE_API_BASE_URL=http://localhost:5000/api
   ```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

Build for production:

```bash
npm run build
```

The production build will be in the `dist/` directory.

### Preview Production Build

Preview the production build locally:

```bash
npm run preview
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `/api` |

## Routes

- `/` - Redirects to `/login` or `/dashboard` based on auth status
- `/login` - User login page
- `/register` - User registration page
- `/onboarding` - Multi-step onboarding flow (protected)
- `/matching` - Match finding and selection (protected)
- `/pod/:pod_id` - Active pod chat interface (protected)
- `/dashboard` - Home page showing active pod or find matches prompt (protected)

## API Integration

The frontend communicates with the backend API through the following endpoints:

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user

### Matching
- `POST /api/matching/find` - Find matches based on match type and focus text
- `POST /api/matching/create-pod` - Create a pod from selected matches

### Pods
- `GET /api/pods/active` - Get user's active pod
- `GET /api/pods/:pod_id` - Get pod details
- `POST /api/pods/:pod_id/leave` - Leave a pod

### Messages
- `GET /api/messages/:pod_id` - Get messages for a pod
- `POST /api/messages/send` - Send a message to a pod

## Features Overview

### Authentication
- Secure JWT-based authentication
- Token persistence in localStorage
- Automatic token refresh on API calls
- Protected routes with navigation guards

### Onboarding
- Welcome screen with app introduction
- Match type selection (Friendship, Goal, Issues)
- Focus text input with character limit
- Automatic match finding after completion

### Matching System
- Displays top 4 matches based on semantic similarity
- Visual similarity score indicators
- Select exactly 3 matches to create a pod
- Real-time match card updates

### Messaging Interface
- Real-time message polling (every 4 seconds)
- 48-hour countdown timer
- Gemini-generated icebreaker explanation
- Message history with timestamps
- Leave pod functionality

### Responsive Design
- Mobile-first approach
- Hamburger menu for mobile navigation
- Responsive grid layouts
- Touch-friendly interface

## Styling

The application uses Tailwind CSS with a custom color scheme:
- **Primary**: `#6366F1` (Indigo)
- **Secondary**: `#8B5CF6` (Purple)
- **Accent**: `#EC4899` (Pink)

Custom fonts: Inter and Poppins from Google Fonts

## State Management

The application uses Pinia for state management with two main stores:

1. **Auth Store** (`stores/auth.js`)
   - User data
   - JWT token
   - Authentication status
   - Login/logout/register actions

2. **Pod Store** (`stores/pod.js`)
   - Active pod data
   - Pod members
   - Pod fetching and management actions

## Development Notes

- All API calls use the configured Axios instance with automatic JWT token injection
- 401 errors automatically redirect to login
- Loading states are handled throughout the application
- Error messages are displayed in user-friendly formats
- Real-time updates use polling (can be upgraded to WebSocket if backend supports it)

## Troubleshooting

### API Connection Issues
- Ensure backend is running on the configured port
- Check `VITE_API_BASE_URL` in `.env`
- Verify CORS settings on backend

### Build Issues
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version compatibility

### Styling Issues
- Ensure Tailwind CSS is properly configured
- Check that PostCSS is installed and configured

## License

Part of the cliqueAI project.

