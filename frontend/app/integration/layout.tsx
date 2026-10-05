import { AuthGuard } from "../components/auth/AuthGuard";

export default function IntegrationLayout({ children }: LayoutProps<"/integration">) {
  return <AuthGuard>{children}</AuthGuard>;
}
