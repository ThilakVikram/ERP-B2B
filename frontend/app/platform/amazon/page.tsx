import { redirect } from "next/navigation";
import { SECTIONS } from "./config";

export default function PlatformAmazonPage() {
  redirect(`/platform/amazon/${SECTIONS[0].slug}`);
}
