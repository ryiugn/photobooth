/**
 * Login Page - PIN Authentication
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';
import { apiService } from '../services/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuthenticated = useAppStore((state) => state.setAuthenticated);
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handlePinChange = (value: string) => {
    if (value.length <= 6 && /^\d*$/.test(value)) {
      setPin(value);
      setError('');
    }
  };

  const handleLogin = async () => {
    if (pin.length < 4) {
      setError('Please enter at least 4 digits');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await apiService.login(pin);
      setAuthenticated(true, response.access_token);
      navigate('/frames');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Incorrect PIN');
      setPin('');
      setIsLoading(false);
    }
  };

  const handleKeyPress = (key: string) => {
    if (key === 'Enter') {
      handleLogin();
    } else if (key === 'Clear') {
      setPin('');
      setError('');
    } else if (key === '⌫') {
      setPin((prev) => prev.slice(0, -1));
      setError('');
    } else {
      handlePinChange(pin + key);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--color-background)',
      padding: 'var(--spacing-lg)',
    }}>
      {/* Title */}
      <h1 style={{
        color: 'var(--color-text)',
        marginBottom: 'var(--spacing-2xl)',
        textAlign: 'center',
      }}>
        PHOTOBOOTH
      </h1>

      {/* PIN Input */}
      <div style={{ width: '100%', maxWidth: '320px' }}>
        <input
          type="password"
          value={pin}
          onChange={(e) => handlePinChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && pin.length >= 4) {
              handleLogin();
            }
          }}
          placeholder="••••"
          maxLength={6}
          style={{
            width: '100%',
            marginBottom: 'var(--spacing-md)',
            letterSpacing: '8px',
          }}
          autoFocus
        />

        {/* Error Message */}
        {error && (
          <p className="text-error" style={{
            textAlign: 'center',
            marginBottom: 'var(--spacing-md)',
            fontSize: 'var(--font-size-sm)',
          }}>
            {error}
          </p>
        )}

        {/* Numeric Keypad */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 'var(--spacing-sm)',
          maxWidth: '280px',
          margin: '0 auto',
        }}>
          {['1', '2', '3', '4', '5', '6', '7', '8', '9', 'Clear', '0', '⌫'].map((key) => (
            <button
              key={key}
              onClick={() => handleKeyPress(key)}
              className="btn"
              style={{
                height: '70px',
                fontSize: 'var(--font-size-xl)',
                backgroundColor: 'var(--color-secondary)',
                color: 'var(--color-text)',
              }}
            >
              {key}
            </button>
          ))}
        </div>

        {/* Enter Button */}
        <button
          onClick={handleLogin}
          disabled={isLoading || pin.length < 4}
          className="btn btn-primary"
          style={{
            width: '100%',
            marginTop: 'var(--spacing-lg)',
            height: '60px',
            fontSize: 'var(--font-size-lg)',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-text-dark)',
          }}
        >
          {isLoading ? '...' : 'ENTER'}
        </button>
      </div>
    </div>
  );
}
