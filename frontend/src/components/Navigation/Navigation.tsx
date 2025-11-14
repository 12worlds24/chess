import { Link, useLocation } from 'react-router-dom';

export default function Navigation() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="bg-gray-800 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-xl font-bold">
              Santrac
            </Link>
            <div className="flex space-x-4">
              <Link
                to="/play"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive('/play')
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                Oyna
              </Link>
              <Link
                to="/puzzles"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive('/puzzles')
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                Bulmaca
              </Link>
              <Link
                to="/learn"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive('/learn')
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                Öğren
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

