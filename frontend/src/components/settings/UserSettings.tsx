import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';

interface UserProfile {
  user: {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar: string | null;
    preferred_ai_provider: string;
    created_at: string;
  };
  profile: {
    id: string;
    risk_level: number;
    favorite_symbols: string[];
    notification_settings: {
      email: boolean;
      push: boolean;
      sms: boolean;
    };
    timezone: string;
  };
}

interface PasswordForm {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export const UserSettings: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'preferences'>('profile');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Profile form state
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [preferredProvider, setPreferredProvider] = useState('ollama');

  // Password form state
  const [passwordForm, setPasswordForm] = useState<PasswordForm>({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Preferences state
  const [riskLevel, setRiskLevel] = useState(5);
  const [timezone, setTimezone] = useState('UTC');
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [smsNotifications, setSmsNotifications] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await apiFetch('/auth/profile/');
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setFirstName(data.user.first_name || '');
        setLastName(data.user.last_name || '');
        setEmail(data.user.email || '');
        setPreferredProvider(data.user.preferred_ai_provider || 'ollama');
        setRiskLevel(data.profile.risk_level || 5);
        setTimezone(data.profile.timezone || 'UTC');
        setEmailNotifications(data.profile.notification_settings?.email ?? true);
        setPushNotifications(data.profile.notification_settings?.push ?? true);
        setSmsNotifications(data.profile.notification_settings?.sms ?? false);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const response = await apiFetch('/auth/profile/update/', {
        method: 'PUT',
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email,
          preferred_ai_provider: preferredProvider,
          risk_level: riskLevel,
          timezone,
          notification_settings: {
            email: emailNotifications,
            push: pushNotifications,
            sms: smsNotifications,
          },
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Profile updated successfully!' });
        fetchProfile();
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || 'Failed to update profile' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    setSaving(true);
    setMessage(null);

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      setSaving(false);
      return;
    }

    try {
      const response = await apiFetch('/auth/change-password/', {
        method: 'POST',
        body: JSON.stringify(passwordForm),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Password changed successfully!' });
        setPasswordForm({ old_password: '', new_password: '', confirm_password: '' });
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || 'Failed to change password' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">User Settings</h2>
        <p className="text-gray-400 mt-1">Manage your account, password, and preferences</p>
      </div>

      {/* Message Toast */}
      {message && (
        <div className={`mb-4 p-4 rounded-lg ${message.type === 'success' ? 'bg-green-500/20 border border-green-500/50 text-green-200' : 'bg-red-500/20 border border-red-500/50 text-red-200'}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-2 text-white/60 hover:text-white">×</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-white/5 p-1 rounded-lg">
        {[
          { id: 'profile' as const, label: '👤 Profile', icon: '' },
          { id: 'password' as const, label: '🔒 Password', icon: '' },
          { id: 'preferences' as const, label: '⚙️ Preferences', icon: '' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-2 px-4 rounded-md transition-all ${activeTab === tab.id ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Personal Information</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">First Name</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter first name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Last Name</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter last name"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter email"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Preferred AI Provider</label>
              <select
                value={preferredProvider}
                onChange={(e) => setPreferredProvider(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="ollama">Ollama (Local)</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="openrouter">OpenRouter</option>
              </select>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={handleSaveProfile}
              disabled={saving}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      {/* Password Tab */}
      {activeTab === 'password' && (
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Change Password</h3>

          <div className="space-y-4 max-w-md">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Current Password</label>
              <input
                type="password"
                value={passwordForm.old_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter current password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">New Password</label>
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter new password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Confirm New Password</label>
              <input
                type="password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Confirm new password"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={handleChangePassword}
              disabled={saving || !passwordForm.old_password || !passwordForm.new_password || !passwordForm.confirm_password}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Changing...' : 'Change Password'}
            </button>
          </div>
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferences' && (
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Trading Preferences</h3>

          <div className="space-y-6">
            {/* Risk Level */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Risk Level: {riskLevel}/10
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={riskLevel}
                onChange={(e) => setRiskLevel(parseInt(e.target.value))}
                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Conservative</span>
                <span>Aggressive</span>
              </div>
            </div>

            {/* Timezone */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Timezone</label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time (ET)</option>
                <option value="America/Chicago">Central Time (CT)</option>
                <option value="America/Denver">Mountain Time (MT)</option>
                <option value="America/Los_Angeles">Pacific Time (PT)</option>
                <option value="Europe/London">London (GMT)</option>
                <option value="Europe/Berlin">Berlin (CET)</option>
                <option value="Asia/Tokyo">Tokyo (JST)</option>
                <option value="Asia/Shanghai">Shanghai (CST)</option>
                <option value="Asia/Dubai">Dubai (GST)</option>
              </select>
            </div>

            {/* Notification Settings */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">Notification Settings</label>
              <div className="space-y-3">
                <label className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                  <div>
                    <span className="text-white">Email Notifications</span>
                    <p className="text-xs text-gray-400">Receive signal alerts via email</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={emailNotifications}
                      onChange={(e) => setEmailNotifications(e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-11 h-6 rounded-full transition-colors ${emailNotifications ? 'bg-purple-600' : 'bg-gray-600'}`}>
                      <div className={`w-5 h-5 rounded-full bg-white shadow transform transition-transform ${emailNotifications ? 'translate-x-5' : 'translate-x-0.5'}`} />
                    </div>
                  </div>
                </label>

                <label className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                  <div>
                    <span className="text-white">Push Notifications</span>
                    <p className="text-xs text-gray-400">Receive push notifications on mobile</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={pushNotifications}
                      onChange={(e) => setPushNotifications(e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-11 h-6 rounded-full transition-colors ${pushNotifications ? 'bg-purple-600' : 'bg-gray-600'}`}>
                      <div className={`w-5 h-5 rounded-full bg-white shadow transform transition-transform ${pushNotifications ? 'translate-x-5' : 'translate-x-0.5'}`} />
                    </div>
                  </div>
                </label>

                <label className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                  <div>
                    <span className="text-white">SMS Notifications</span>
                    <p className="text-xs text-gray-400">Receive critical alerts via SMS</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={smsNotifications}
                      onChange={(e) => setSmsNotifications(e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-11 h-6 rounded-full transition-colors ${smsNotifications ? 'bg-purple-600' : 'bg-gray-600'}`}>
                      <div className={`w-5 h-5 rounded-full bg-white shadow transform transition-transform ${smsNotifications ? 'translate-x-5' : 'translate-x-0.5'}`} />
                    </div>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={handleSaveProfile}
              disabled={saving}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
          </div>
        </div>
      )}

      {/* Account Info */}
      {profile && (
        <div className="mt-6 bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Account Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Username:</span>
              <span className="ml-2 text-white">{profile.user.username}</span>
            </div>
            <div>
              <span className="text-gray-400">User ID:</span>
              <span className="ml-2 text-white font-mono text-xs">{profile.user.id}</span>
            </div>
            <div>
              <span className="text-gray-400">Member Since:</span>
              <span className="ml-2 text-white">{new Date(profile.user.created_at).toLocaleDateString()}</span>
            </div>
            <div>
              <span className="text-gray-400">Status:</span>
              <span className="ml-2 text-green-400">✓ Verified</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserSettings;
