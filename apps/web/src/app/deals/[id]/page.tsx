import { loadDealWorkbench } from "./data";
import { DealWorkbench } from "./workbench";

export const dynamic = "force-dynamic";

type DealPageProps = {
  readonly params: Promise<{
    readonly id: string;
  }>;
  readonly searchParams: Promise<{
    readonly as_of?: string | readonly string[];
  }>;
};

function firstSearchValue(value: string | readonly string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function DealPage({ params, searchParams }: DealPageProps) {
  const { id } = await params;
  const { as_of } = await searchParams;
  const data = await loadDealWorkbench(id, firstSearchValue(as_of));

  if (data.kind === "setup_required") {
    return (
      <main className="app-shell">
        <section className="panel setup-panel">
          <div className="panel-header">
            <p>production</p>
            <h1>Configuration required</h1>
          </div>
          <div className="panel-body">
            <p>{data.message}</p>
          </div>
        </section>
      </main>
    );
  }

  return <DealWorkbench briefing={data.briefing} contexts={data.contexts} selectedContext={data.selectedContext} timeline={data.timeline} />;
}
