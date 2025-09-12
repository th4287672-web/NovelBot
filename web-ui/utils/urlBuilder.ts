import type { Character, UserInfo } from '~/types/api';

interface ImageResource {
  image?: string | null;
  avatar?: string | null;
  owner_id?: string | null;
  user_id?: string;
  is_private?: boolean;
}

export function getResourceUrl(item: Partial<ImageResource> | null): string | null {
  if (!item) return null;

  const config = useRuntimeConfig();
  const imageUrl = item.image ?? item.avatar;

  if (!imageUrl) {
    return null;
  }

  if (imageUrl.startsWith('http') || imageUrl.startsWith('data:') || imageUrl.startsWith('blob:')) {
    return imageUrl;
  }

  if (imageUrl.startsWith('/api/')) {
    const apiBase = config.public.apiBase || 'http://localhost:8080';
    return `${apiBase}${imageUrl}`;
  }

  return imageUrl;
}