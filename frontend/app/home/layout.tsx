import { AuthGuard } from "../components/auth/AuthGuard";

export default function HomeLayout({ children }: LayoutProps<"/home">) {
  return <AuthGuard>{children}</AuthGuard>;
}
