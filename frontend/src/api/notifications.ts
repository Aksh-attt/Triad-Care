import apiClient from './client';
import type { Notification } from '../types';

export const getNotifications = async (profileId: number): Promise<Notification[]> => {
  const { data } = await apiClient.get(`/api/notifications/${profileId}`);
  return data;
};

export const markNotificationRead = async (notificationId: number): Promise<Notification> => {
  const { data } = await apiClient.put(`/api/notifications/${notificationId}/read`);
  return data;
};

export const markAsRead = markNotificationRead;

export const markAllRead = async (profileId: number): Promise<void> => {
  await apiClient.put(`/api/notifications/${profileId}/read-all`);
};

export const markAllAsRead = markAllRead;
