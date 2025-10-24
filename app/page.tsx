import { AnaRagChat } from "@/components/ana-rag-chat"

export default function Home() {
  return (
    <main
      className="min-h-screen animate-fade-in"
      style={{ background: "linear-gradient(135deg, #E8F5FF 0%, #F0FFF4 100%)" }}
    >
      <AnaRagChat />
    </main>
  )
}
