import { redirect } from "next/navigation";
import { PLATFORMS } from "./config";

export default function PlatformPage() {
  redirect(`/platform/${PLATFORMS[0].slug}`);
}
