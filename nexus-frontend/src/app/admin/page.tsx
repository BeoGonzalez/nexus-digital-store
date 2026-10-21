import { DollarSign, Users, Gamepad2, Activity } from "lucide-react";

export default function AdminDashboard() {
  const metrics = [
    { title: "Ingresos Totales", value: "$12.450.000", change: "+14%", icon: DollarSign, trend: "up" },
    { title: "Usuarios Activos", value: "2,345", change: "+5%", icon: Users, trend: "up" },
    { title: "Juegos en Catálogo", value: "142", change: "+12", icon: Gamepad2, trend: "up" },
    { title: "Sesiones Activas", value: "34", change: "-2%", icon: Activity, trend: "down" },
  ];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8">
        <h1 className="text-3xl font-black tracking-tight">Dashboard General</h1>
        <p className="text-white/50 mt-1">Bienvenido de vuelta, administrador.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, i) => {
          const Icon = metric.icon;
          return (
            <div key={i} className="rounded-2xl border border-white/5 bg-[#121418] p-6 transition-all hover:bg-white/5 hover:border-white/10">
              <div className="flex items-center justify-between mb-4">
                <div className="size-10 rounded-xl bg-white/5 flex items-center justify-center text-[#48c8d8]">
                  <Icon size={20} />
                </div>
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                  metric.trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                }`}>
                  {metric.change}
                </span>
              </div>
              <p className="text-sm font-medium text-white/50">{metric.title}</p>
              <h3 className="text-2xl font-black mt-1">{metric.value}</h3>
            </div>
          );
        })}
      </div>

      <div className="mt-10 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-3xl border border-white/5 bg-[#121418] p-8">
          <h3 className="text-lg font-bold mb-6">Actividad Reciente</h3>
          <div className="flex flex-col items-center justify-center py-12 text-white/30">
            <Activity size={48} className="mb-4 opacity-20" />
            <p className="text-sm">Gráfico de actividad en desarrollo</p>
          </div>
        </div>
        <div className="rounded-3xl border border-white/5 bg-[#121418] p-8">
          <h3 className="text-lg font-bold mb-6">Últimas Compras</h3>
          <div className="space-y-6">
            {[1, 2, 3].map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="size-10 rounded-full bg-white/5 flex items-center justify-center text-white/50">
                  <Users size={16} />
                </div>
                <div>
                  <p className="text-sm font-bold">Orden #00{i+1}</p>
                  <p className="text-xs text-white/50">Hace {i+2} horas</p>
                </div>
                <div className="ml-auto font-bold text-sm text-[#48c8d8]">
                  $45.000
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
