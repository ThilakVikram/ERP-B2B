import { AuthGuard } from "../components/auth/AuthGuard";

export default function SalesLayout({ children }: LayoutProps<"/sales">) {
  return <AuthGuard>{children}</AuthGuard>;
}
