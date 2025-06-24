import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, User, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react';
const heroImage = '/canary.webp';
import { loginUser, registerUser } from '../../services/auth-service';
import { useAuth } from '../../context/AuthContext';

const CanaryInput = ({ id, name, type, placeholder, value, onChange, icon: Icon, showPasswordToggle = false }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="relative group">
      <Icon className={`absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 z-10 transition-colors duration-200 ${
        isFocused ? 'text-yellow-400' : 'text-yellow-400/70'
      }`} />
      <input
        type={showPasswordToggle && showPassword ? 'text' : type}
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        required
        placeholder={placeholder}
        className={`w-full bg-gradient-to-r from-black/40 to-black/20 border text-white rounded-2xl py-4 pl-12 pr-12 backdrop-blur-xl placeholder:text-yellow-100/60 transition-all duration-300 ease-out ${
          isFocused 
            ? 'border-yellow-400/50 shadow-lg shadow-yellow-400/10 bg-gradient-to-r from-black/50 to-black/30' 
            : 'border-yellow-400/20 hover:border-yellow-400/30'
        }`}
      />
      {showPasswordToggle && (
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-yellow-400/70 hover:text-yellow-400 transition-colors duration-200"
        >
          {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
        </button>
      )}
    </div>
  );
};

export default function CanaryLogin() {
  const { login } = useAuth();
  const [isLoginView, setIsLoginView] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', username: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });
  const toggleView = () => {
    setIsLoginView(!isLoginView);
    setFormData({ email: '', password: '', username: '' });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = isLoginView
        ? await loginUser(formData.email, formData.password)
        : await registerUser(formData.email, formData.password, formData.username);
      login(res);
    } catch (err) {
      setError(err.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black flex items-center justify-center px-4 overflow-hidden">
      {/* Subtle background glow */}
      <div className="absolute inset-0 bg-gradient-to-r from-yellow-400/5 via-transparent to-yellow-400/5 blur-3xl" />
      
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-5xl bg-gradient-to-br from-black/30 via-black/20 to-black/40 border border-yellow-400/10 backdrop-blur-2xl rounded-3xl overflow-hidden shadow-2xl shadow-black/50"
        style={{
          background: 'linear-gradient(135deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0.3) 100%)',
          backdropFilter: 'blur(40px)',
          WebkitBackdropFilter: 'blur(40px)',
        }}
      >
        <div className="grid md:grid-cols-2 items-stretch gap-0 min-h-[600px]">
          {/* Left: Hero Image Section */}
          <div className="relative w-full h-full">
            <img
              src={heroImage}
              alt="Signup Visual"
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-black/60" />
            <div className="absolute bottom-12 left-10 text-yellow-100">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.6 }}
              >
                <h2 className="text-3xl font-semibold mb-3 text-white">Tip</h2>
                <p className="text-yellow-300/90 text-sm w-64 leading-relaxed">
                  Talk to Canary to set what it should keep an eye on.
                </p>
              </motion.div>
            </div>
          </div>

          {/* Right: Form Section */}
          <div className="p-12 relative">
            {/* Subtle gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-black/20 via-transparent to-black/30 pointer-events-none" />
            
            <div className="relative z-10">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.6 }}
              >
                <h2 className="text-3xl font-medium text-white mb-8 tracking-tight">
                  {isLoginView ? 'Sign in' : 'Sign up'}
                </h2>
              </motion.div>

              <motion.form 
                onSubmit={handleSubmit} 
                className="space-y-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4, duration: 0.6 }}
              >
                <CanaryInput
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleChange}
                  icon={Mail}
                />
                {!isLoginView && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <CanaryInput
                      id="username"
                      name="username"
                      type="text"
                      placeholder="Username"
                      value={formData.username}
                      onChange={handleChange}
                      icon={User}
                    />
                  </motion.div>
                )}
                <CanaryInput
                  id="password"
                  name="password"
                  type="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleChange}
                  icon={Lock}
                  showPasswordToggle
                />

                {error && (
                  <motion.div 
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-3 text-red-300 text-sm bg-red-500/10 border border-red-500/20 p-4 rounded-2xl backdrop-blur-sm"
                  >
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </motion.div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-yellow-400/90 to-yellow-500/90 text-black font-semibold py-4 rounded-2xl hover:from-yellow-400/95 hover:to-yellow-500/95 transition-all duration-300 ease-out transform hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-yellow-400/15 backdrop-blur-sm border border-yellow-400/20 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {loading ? (
                    <span className="flex justify-center items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      {isLoginView ? 'Signing in...' : 'Creating account...'}
                    </span>
                  ) : (
                    isLoginView ? 'Sign In' : 'Create Account'
                  )}
                </button>
              </motion.form>

              <motion.div 
                className="mt-8 text-center text-sm text-yellow-100/80"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.6 }}
              >
                {isLoginView ? "Don't have an account?" : 'Already registered?'}{' '}
                <button
                  onClick={toggleView}
                  className="text-yellow-400 font-medium hover:text-yellow-300 transition-colors duration-200 hover:underline"
                >
                  {isLoginView ? 'Create Account' : 'Sign In'}
                </button>
              </motion.div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}