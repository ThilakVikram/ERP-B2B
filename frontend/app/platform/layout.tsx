import { AuthGuard } from "../components/auth/AuthGuard";

export default function PlatformLayout({ children }: LayoutProps<"/platform">) {
  return <AuthGuard>{children}</AuthGuard>;
}
