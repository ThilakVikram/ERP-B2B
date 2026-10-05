import { redirect } from "next/navigation";
import { SECTIONS } from "./config";

export default function AmazonIntegrationPage() {
  redirect(`/integration/amazon/${SECTIONS[0].slug}`);
}
