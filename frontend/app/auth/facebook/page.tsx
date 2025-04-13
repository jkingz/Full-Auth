'use client';

import { Spinner } from '@/components/common';
import { useSocialAuth } from '@/hooks';
import { useSocialAuthenticateMutation } from '@/redux/features/authApiSlice';

export default function Page() {
  const [facebookAuthenticate] = useSocialAuthenticateMutation();
  useSocialAuth(facebookAuthenticate, 'facebook');

  return (
    <div className="my-8">
      <Spinner lg />
    </div>
  );
}
