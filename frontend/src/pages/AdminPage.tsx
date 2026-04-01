import React, { useEffect, useState } from 'react';
import { adminApi } from '../services/api';
import { User, Meeting } from '../types';
import Navbar from '../components/Navbar';

interface DashboardStats {
  total_users: number;
  total_meetings: number;
  recent_users: User[];
  recent_meetings: Meeting[];
}

const AdminPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'meetings'>('overview');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => { loadDashboard(); }, []);

  const loadDashboard = async () => {
    setIsLoading(true);
    try { const response = await adminApi.getDashboard(); setStats(response.data); }
    catch (error) { console.error('Failed to load dashboard:', error); }
    finally { setIsLoading(false); }
  };

  const loadUsers = async () => {
    setIsLoading(true);
    try { const response = await adminApi.getUsers(); setUsers(response.data); }
    catch (error) { console.error('Failed to load users:', error); }
    finally { setIsLoading(false); }
  };

  const loadMeetings = async () => {
    setIsLoading(true);
    try { const response = await adminApi.getMeetings(); setMeetings(response.data); }
    catch (error) { console.error('Failed to load meetings:', error); }
    finally { setIsLoading(false); }
  };

  const handleDeactivateUser = async (userId: number) => {
    if (!window.confirm('Are you sure you want to deactivate this user?')) return;
    try { await adminApi.deactivateUser(userId); loadUsers(); }
    catch (error) { console.error('Failed to deactivate user:', error); }
  };

  const handleTabChange = (tab: 'overview' | 'users' | 'meetings') => {
    setActiveTab(tab);
    if (tab === 'users' && users.length === 0) loadUsers();
    if (tab === 'meetings' && meetings.length === 0) loadMeetings();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
        <div className="border-b mb-6">
          <div className="flex space-x-8">
            {(['overview', 'users', 'meetings'] as const).map((tab) => (
              <button key={tab} onClick={() => handleTabChange(tab)} className={`pb-4 font-medium capitalize ${activeTab === tab ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500 hover:text-gray-700'}`}>{tab}</button>
            ))}
          </div>
        </div>
        {isLoading ? <div className="text-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div></div> : (
          <>
            {activeTab === 'overview' && stats && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white rounded-lg shadow p-6"><div className="text-3xl font-bold text-primary-600">{stats.total_users}</div><div className="text-gray-500">Total Users</div></div>
                  <div className="bg-white rounded-lg shadow p-6"><div className="text-3xl font-bold text-primary-600">{stats.total_meetings}</div><div className="text-gray-500">Total Meetings</div></div>
                </div>
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b"><h3 className="font-semibold">Recent Users</h3></div>
                  <div className="divide-y">{stats.recent_users.map((user) => (
                    <div key={user.id} className="px-6 py-4 flex justify-between items-center">
                      <div><div className="font-medium">{user.full_name}</div><div className="text-sm text-gray-500">{user.email}</div></div>
                      <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{user.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                  ))}</div>
                </div>
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b"><h3 className="font-semibold">Recent Meetings</h3></div>
                  <div className="divide-y">{stats.recent_meetings.map((meeting) => (
                    <div key={meeting.id} className="px-6 py-4">
                      <div className="font-medium">{meeting.name}</div>
                      <div className="text-sm text-gray-500">Status: {meeting.status} | Created: {new Date(meeting.created_at).toLocaleDateString()}</div>
                    </div>
                  ))}</div>
                </div>
              </div>
            )}
            {activeTab === 'users' && (
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b"><h3 className="font-semibold">All Users</h3></div>
                <div className="divide-y">{users.map((user) => (
                  <div key={user.id} className="px-6 py-4 flex justify-between items-center">
                    <div><div className="font-medium">{user.full_name}</div><div className="text-sm text-gray-500">{user.email}</div><div className="text-xs text-gray-400">Joined: {new Date(user.created_at).toLocaleDateString()}</div></div>
                    <div className="flex items-center space-x-2">
                      {user.is_superadmin && <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">Admin</span>}
                      <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{user.is_active ? 'Active' : 'Inactive'}</span>
                      {user.is_active && !user.is_superadmin && <button onClick={() => handleDeactivateUser(user.id)} className="text-red-600 hover:text-red-800 text-sm">Deactivate</button>}
                    </div>
                  </div>
                ))}</div>
              </div>
            )}
            {activeTab === 'meetings' && (
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b"><h3 className="font-semibold">All Meetings</h3></div>
                <div className="divide-y">{meetings.map((meeting) => (
                  <div key={meeting.id} className="px-6 py-4">
                    <div className="font-medium">{meeting.name}</div>
                    <div className="text-sm text-gray-500">Status: {meeting.status} | Created: {new Date(meeting.created_at).toLocaleDateString()}</div>
                  </div>
                ))}</div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AdminPage;
