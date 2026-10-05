import { AuthGuard } from "../components/auth/AuthGuard";

export default function InventoryLayout({ children }: LayoutProps<"/inventory">) {
  return <AuthGuard>{children}</AuthGuard>;
}
