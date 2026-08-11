import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
} from 'react-native';
import { THEME } from '../../App';

export default function SettingsScreen({ navigation }: any) {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [autoTrading, setAutoTrading] = useState(false);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
        <Text style={styles.subtitle}>Configure your app</Text>
      </View>

      {/* Account Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account</Text>
        <View style={styles.settingsCard}>
          <TouchableOpacity style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>Profile</Text>
            <Text style={styles.settingsValue}>→</Text>
          </TouchableOpacity>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>API Keys</Text>
            <Text style={styles.settingsValue}>→</Text>
          </TouchableOpacity>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>Subscription</Text>
            <Text style={[styles.settingsValue, { color: THEME.primary }]}>Pro</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Trading Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Trading</Text>
        <View style={styles.settingsCard}>
          <View style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>Auto-Trading</Text>
            <Switch
              value={autoTrading}
              onValueChange={setAutoTrading}
              trackColor={{ false: THEME.card, true: THEME.success + '80' }}
              thumbColor={autoTrading ? THEME.success : THEME.textSecondary}
            />
          </View>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>Risk Level</Text>
            <Text style={styles.settingsValue}>Moderate</Text>
          </TouchableOpacity>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>Default Pair</Text>
            <Text style={styles.settingsValue}>BTC/USDT</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Notifications Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notifications</Text>
        <View style={styles.settingsCard}>
          <View style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>Push Notifications</Text>
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{ false: THEME.card, true: THEME.primary + '80' }}
              thumbColor={notificationsEnabled ? THEME.primary : THEME.textSecondary}
            />
          </View>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>Alert Preferences</Text>
            <Text style={styles.settingsValue}>→</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* App Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>App</Text>
        <View style={styles.settingsCard}>
          <View style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>Dark Mode</Text>
            <Switch
              value={darkMode}
              onValueChange={setDarkMode}
              trackColor={{ false: THEME.card, true: THEME.primary + '80' }}
              thumbColor={darkMode ? THEME.primary : THEME.textSecondary}
            />
          </View>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.settingsItem}>
            <Text style={styles.settingsLabel}>About</Text>
            <Text style={styles.settingsValue}>v1.0.0</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Logout */}
      <TouchableOpacity
        style={styles.logoutButton}
        onPress={() => navigation.getParent()?.navigate('Login')}
      >
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.background,
  },
  header: {
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: THEME.text,
  },
  subtitle: {
    fontSize: 14,
    color: THEME.textSecondary,
    marginTop: 4,
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME.textSecondary,
    marginBottom: 12,
  },
  settingsCard: {
    backgroundColor: THEME.surface,
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingsItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  settingsLabel: {
    fontSize: 16,
    color: THEME.text,
  },
  settingsValue: {
    fontSize: 14,
    color: THEME.textSecondary,
  },
  divider: {
    height: 1,
    backgroundColor: THEME.border,
    marginLeft: 16,
  },
  logoutButton: {
    margin: 16,
    padding: 16,
    backgroundColor: THEME.danger + '20',
    borderRadius: 12,
    alignItems: 'center',
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME.danger,
  },
});
