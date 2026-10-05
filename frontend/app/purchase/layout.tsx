import { AuthGuard } from "../components/auth/AuthGuard";

export default function PurchaseLayout({ children }: LayoutProps<"/purchase">) {
  return <AuthGuard>{children}</AuthGuard>;
}
