import axios from 'axios';
import type {
  Channel,
  Video,
  VideoMetrics,
  ChannelMetrics,
  TrendingVideo,
  AddChannelRequest,
  AddChannelResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Channels API
export const channelsApi = {
  list: async (isOwnChannel?: boolean): Promise<Channel[]> => {
    const params = isOwnChannel !== undefined ? { is_own_channel: isOwnChannel } : {};
    const response = await api.get('/api/v1/channels', { params });
    return response.data;
  },

  get: async (id: number): Promise<Channel> => {
    const response = await api.get(`/api/v1/channels/${id}`);
    return response.data;
  },

  add: async (data: AddChannelRequest): Promise<AddChannelResponse> => {
    const response = await api.post('/api/v1/channels', data);
    return response.data;
  },

  updateStats: async (id: number): Promise<Channel> => {
    const response = await api.post(`/api/v1/channels/${id}/update-stats`);
    return response.data;
  },

  getVideos: async (id: number): Promise<Video[]> => {
    const response = await api.get(`/api/v1/channels/${id}/videos`);
    return response.data;
  },

  importVideos: async (id: number, maxVideos?: number): Promise<{ message: string; task_id: string }> => {
    const params = maxVideos ? { max_videos: maxVideos } : {};
    const response = await api.post(`/api/v1/channels/${id}/import-videos`, null, { params });
    return response.data;
  },
};

// Videos API
export const videosApi = {
  get: async (id: number): Promise<Video> => {
    const response = await api.get(`/api/v1/videos/${id}`);
    return response.data;
  },

  updateStats: async (id: number): Promise<Video> => {
    const response = await api.post(`/api/v1/videos/${id}/update-stats`);
    return response.data;
  },
};

// Analytics API
export const analyticsApi = {
  getVideoMetrics: async (id: number): Promise<VideoMetrics> => {
    const response = await api.get(`/api/v1/analytics/videos/${id}/metrics`);
    return response.data;
  },

  getChannelMetrics: async (id: number): Promise<ChannelMetrics> => {
    const response = await api.get(`/api/v1/analytics/channels/${id}/metrics`);
    return response.data;
  },

  getTrendingVideos: async (hours?: number, channelId?: number, limit?: number): Promise<TrendingVideo[]> => {
    const params: any = {};
    if (hours) params.hours = hours;
    if (channelId) params.channel_id = channelId;
    if (limit) params.limit = limit;
    const response = await api.get('/api/v1/analytics/trending/videos', { params });
    return response.data;
  },

  compareChannels: async (channelIds: number[]): Promise<ChannelMetrics[]> => {
    const response = await api.get('/api/v1/analytics/compare/channels', {
      params: { channel_ids: channelIds.join(',') },
    });
    return response.data;
  },
};

export default api;
