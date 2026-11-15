import apiClient from './client';
import type { Appointment } from '../types';

export const getAppointments = async (profileId: number): Promise<Appointment[]> => {
  const { data } = await apiClient.get(`/api/appointments/${profileId}`);
  return data;
};

export const addAppointment = async (profileId: number, appointment: Partial<Appointment>): Promise<Appointment> => {
  const { data } = await apiClient.post(`/api/appointments/${profileId}`, appointment);
  return data;
};

export const updateAppointment = async (appointmentId: number, updates: Partial<Appointment>): Promise<Appointment> => {
  const { data } = await apiClient.put(`/api/appointments/${appointmentId}`, updates);
  return data;
};

export const deleteAppointment = async (appointmentId: number): Promise<void> => {
  await apiClient.delete(`/api/appointments/${appointmentId}`);
};
