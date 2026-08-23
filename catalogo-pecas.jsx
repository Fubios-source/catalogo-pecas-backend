import React, { useState, useEffect, useRef } from "react";
import { Camera, ShoppingBag, MessageCircle, Loader2, X, Edit3, Trash2, Package, AlertTriangle, Check, Settings, Search, Car } from "lucide-react";

const FONT_STYLE = `
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

.cp-root { font-family: 'Inter', sans-serif; }
.cp-display { font-family: 'Oswald', sans-serif; text-transform: uppercase; letter-spacing: 0.02em; }
.cp-mono { font-family: 'IBM Plex Mono', monospace; }

.cp-scan-line {
  background: repeating-linear-gradient(45deg, rgba(255,182,39,0.06) 0px, rgba(255,182,39,0.06) 2px, transparent 2px, transparent 10px);
}

.cp-plate {
  background: linear-gradient(155deg, #2A2E36 0%, #1C1F24 60%);
  border: 1px dashed #454B55;
}

.cp-focus:focus-visible {
  outline: 2px solid #FFB627;
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .cp-anim { animation: none !important; transition: none !important; }
}

@keyframes cp-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
.cp-pulse { animation: cp-pulse 1.4s ease-in-out infinite; }

@keyframes cp-scan {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}
.cp-scanner { animation: cp-scan 1.8s linear infinite; }
`;

const CATALOG_KEY = "catalog-items";
const CONFIG_KEY = "catalog-config";
const MEMBER_KEY = "catalog-member-name";

function resizeImage(file, maxWidth = 640, quality = 0.72) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const scale = Math.min(1, maxWidth / img.width);
        const canvas = document.createElement("canvas");
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL("image/jpeg", quality);
        resolve(dataUrl);
      };
      img.onerror = reject;
      img.src = e.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function dataUrlToBase64(dataUrl) {
  const [meta, data] = dataUrl.split(",");
  const mime = meta.match(/data:(.*);base64/)[1];
  return { mime, data };
}

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

async function identifyPart(dataUrl) {
  const { mime, data } = dataUrlToBase64(dataUrl);
  
  // Converte base64 pra Blob e depois File pra multipart/form-data
  const byteString = atob(data);
  const byteArray = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i++) {
    byteArray[i] = byteString.charCodeAt(i);
  }
  const blob = new Blob([byteArray], { type: mime });

  const formData = new FormData();
  formData.append("file", blob, "part.jpg");

  const response = await fetch(`${API_BASE}/identify-part-by-photo`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Falha ao identificar peça");
  }

  const json = await response.json();
  if (!json.success) throw new Error("Falha ao processar resposta");
  return json.data;
}

async function searchByVehicle({ peca, montadora, modelo, ano, motor }) {
  const formData = new FormData();
  formData.append("peca", peca);
  formData.append("montadora", montadora);
  formData.append("modelo", modelo);
  if (ano) formData.append("ano", ano);
  if (motor) formData.append("motor", motor);

  const response = await fetch(`${API_BASE}/search-part-by-vehicle`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Falha ao buscar peça");
  }

  const json = await response.json();
  if (!json.success) throw new Error("Falha ao processar resposta");
  return json.data;
}

function Chip({ children }) {
  return (
    <span className="cp-plate cp-mono inline-block px-2 py-1 text-[11px] rounded text-amber-300 mr-1.5 mb-1.5">
      {children}
    </span>
  );
}

function Header({ view, setView, itemCount }) {
  return (
    <div className="sticky top-0 z-20 bg-[#14161A]/95 backdrop-blur border-b border-[#2A2E36] px-4 pt-4 pb-0">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="cp-display text-xl text-white leading-none">Bancada</h1>
          <p className="text-[11px] text-[#8B92A0] mt-1">catálogo de peças por foto</p>
        </div>
        <div className="cp-plate w-9 h-9 rounded-md flex items-center justify-center">
          <Package size={16} className="text-amber-400" />
        </div>
      </div>
      <div className="flex gap-1">
        {[
          { id: "capture", label: "Foto", icon: Camera },
          { id: "vehicle", label: "Por veículo", icon: Car },
          { id: "catalog", label: `Catálogo (${itemCount})`, icon: ShoppingBag },
          { id: "config", label: "Config", icon: Settings },
        ].map((t) => {
          const Icon = t.icon;
          const active = view === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setView(t.id)}
              className={`cp-focus flex items-center gap-1.5 px-3 py-2.5 text-[13px] font-medium border-b-2 transition-colors whitespace-nowrap ${
                active ? "border-amber-400 text-white" : "border-transparent text-[#8B92A0] hover:text-white"
              }`}
            >
              <Icon size={14} />
              {t.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function CaptureView({ memberName, setMemberName, onSaved }) {
  const [photo, setPhoto] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | analyzing | done | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [preco, setPreco] = useState("");
  const [saving, setSaving] = useState(false);
  const fileRef = useRef(null);

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setStatus("analyzing");
    setResult(null);
    setErrorMsg("");
    try {
      const resized = await resizeImage(file);
      setPhoto(resized);
      const data = await identifyPart(resized);
      setResult(data);
      setStatus("done");
    } catch (err) {
      console.error(err);
      setErrorMsg("Não consegui analisar essa foto. Tenta de novo com mais luz e a peça mais próxima da câmera.");
      setStatus("error");
    }
  };

  const reset = () => {
    setPhoto(null);
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
    setPreco("");
    if (fileRef.current) fileRef.current.value = "";
  };

  const salvar = async () => {
    if (!result) return;
    setSaving(true);
    try {
      let current = [];
      try {
        const existing = await window.storage.get(CATALOG_KEY, true);
        current = existing ? JSON.parse(existing.value) : [];
      } catch (_) {
        current = [];
      }
      const novoItem = {
        id: `item_${Date.now()}`,
        foto: photo,
        preco: preco || null,
        autor: memberName || "sem nome",
        criadoEm: new Date().toISOString(),
        ...result,
      };
      const atualizado = [novoItem, ...current];
      const saveResult = await window.storage.set(CATALOG_KEY, JSON.stringify(atualizado), true);
      if (!saveResult) throw new Error("Falha ao salvar");
      onSaved();
      reset();
    } catch (err) {
      console.error(err);
      setErrorMsg("Não consegui salvar no catálogo. Tenta de novo.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="px-4 py-5 pb-24">
      {!memberName && (
        <div className="cp-plate rounded-lg p-3 mb-4">
          <label className="text-[11px] text-[#8B92A0] block mb-1.5">Seu nome (aparece em quem cadastrou)</label>
          <input
            className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2 text-sm text-white"
            placeholder="ex: Fabio"
            onBlur={(e) => e.target.value && setMemberName(e.target.value)}
          />
        </div>
      )}

      {status === "idle" && (
        <div className="cp-plate cp-scan-line rounded-xl p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[#14161A] border border-amber-400/40 flex items-center justify-center">
            <Camera size={26} className="text-amber-400" />
          </div>
          <h2 className="cp-display text-lg text-white mb-1.5">Aponte pra peça</h2>
          <p className="text-[13px] text-[#8B92A0] mb-5 leading-relaxed max-w-xs mx-auto">
            Tira a foto com boa luz, peça inteira no quadro. A IA identifica o tipo, código OEM provável e aplicação.
          </p>
          <label className="cp-focus inline-flex items-center gap-2 bg-amber-400 hover:bg-amber-300 text-[#14161A] font-semibold text-sm px-5 py-3 rounded-lg cursor-pointer transition-colors">
            <Camera size={16} />
            Tirar / escolher foto
            <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={handleFile} />
          </label>
        </div>
      )}

      {status === "analyzing" && (
        <div className="cp-plate rounded-xl p-6 text-center relative overflow-hidden">
          {photo && <img src={photo} alt="analisando" className="w-full h-56 object-cover rounded-lg mb-4 opacity-70" />}
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-b from-amber-400/60 to-transparent cp-scanner cp-anim" />
          <div className="flex items-center justify-center gap-2 text-amber-300">
            <Loader2 size={16} className="animate-spin" />
            <span className="cp-mono text-[13px] cp-pulse cp-anim">analisando peça...</span>
          </div>
        </div>
      )}

      {status === "error" && (
        <div className="cp-plate rounded-xl p-6 text-center border-red-500/40">
          <AlertTriangle size={22} className="text-red-400 mx-auto mb-2" />
          <p className="text-[13px] text-[#C9CDD4] mb-4">{errorMsg}</p>
          <button onClick={reset} className="cp-focus text-sm text-amber-400 font-medium">Tentar de novo</button>
        </div>
      )}

      {status === "done" && result && (
        <div>
          <div className="relative rounded-xl overflow-hidden mb-4">
            <img src={photo} alt={result.nome} className="w-full h-56 object-cover" />
            <button
              onClick={reset}
              className="cp-focus absolute top-2 right-2 w-8 h-8 rounded-full bg-black/60 flex items-center justify-center text-white"
              aria-label="Descartar foto"
            >
              <X size={15} />
            </button>
          </div>

          <div className="flex items-start justify-between mb-1">
            <span className="text-[11px] cp-mono uppercase tracking-wide text-[#8B92A0]">{result.categoria}</span>
            <span
              className={`text-[10px] cp-mono uppercase px-2 py-0.5 rounded ${
                result.confianca === "alta"
                  ? "bg-green-500/15 text-green-400"
                  : result.confianca === "média"
                  ? "bg-amber-500/15 text-amber-400"
                  : "bg-red-500/15 text-red-400"
              }`}
            >
              confiança {result.confianca}
            </span>
          </div>
          <h2 className="cp-display text-xl text-white mb-3">{result.nome}</h2>

          {result.codigos_oem_provaveis?.length > 0 && (
            <div className="mb-3">
              <p className="text-[11px] text-[#8B92A0] mb-1.5">Códigos OEM prováveis</p>
              <div className="flex flex-wrap">
                {result.codigos_oem_provaveis.map((c, i) => <Chip key={i}>{c}</Chip>)}
              </div>
            </div>
          )}

          {result.aplicacoes_provaveis?.length > 0 && (
            <div className="mb-3">
              <p className="text-[11px] text-[#8B92A0] mb-1.5">Aplicações prováveis</p>
              <ul className="text-[13px] text-[#C9CDD4] space-y-1">
                {result.aplicacoes_provaveis.map((a, i) => <li key={i}>• {a}</li>)}
              </ul>
            </div>
          )}

          {result.observacoes && (
            <div className="mb-4">
              <p className="text-[11px] text-[#8B92A0] mb-1">Observações</p>
              <p className="text-[13px] text-[#C9CDD4] leading-relaxed">{result.observacoes}</p>
            </div>
          )}

          <p className="text-[11px] text-[#6B7280] mb-4 italic">
            Isso é um palpite da IA a partir da foto — confirma o código antes de vender, principalmente se a confiança não for alta.
          </p>

          <div className="mb-4">
            <label className="text-[11px] text-[#8B92A0] block mb-1.5">Preço (opcional)</label>
            <input
              className="cp-focus w-full bg-[#1C1F24] border border-[#3A3F48] rounded-lg px-3 py-2.5 text-sm text-white"
              placeholder="R$ 0,00"
              value={preco}
              onChange={(e) => setPreco(e.target.value)}
            />
          </div>

          {errorMsg && <p className="text-[12px] text-red-400 mb-3">{errorMsg}</p>}

          <div className="flex gap-2">
            <button onClick={reset} className="cp-focus flex-1 py-3 rounded-lg border border-[#3A3F48] text-[#C9CDD4] text-sm font-medium">
              Descartar
            </button>
            <button
              onClick={salvar}
              disabled={saving}
              className="cp-focus flex-[2] py-3 rounded-lg bg-amber-400 hover:bg-amber-300 disabled:opacity-60 text-[#14161A] text-sm font-semibold flex items-center justify-center gap-2"
            >
              {saving ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />}
              Adicionar ao catálogo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function EditModal({ item, onClose, onSave, onDelete }) {
  const [preco, setPreco] = useState(item.preco || "");
  const [nome, setNome] = useState(item.nome || "");

  return (
    <div className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center" onClick={onClose}>
      <div className="cp-plate w-full sm:max-w-sm rounded-t-2xl sm:rounded-2xl p-5 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="cp-display text-white text-base">Editar item</h3>
          <button onClick={onClose} className="cp-focus text-[#8B92A0]"><X size={18} /></button>
        </div>
        
        <label className="text-[11px] text-[#8B92A0] block mb-1.5">Nome</label>
        <input
          className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2 text-sm text-white mb-3"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
        />
        
        <label className="text-[11px] text-[#8B92A0] block mb-1.5">Preço</label>
        <input
          className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2 text-sm text-white mb-3"
          value={preco}
          onChange={(e) => setPreco(e.target.value)}
          placeholder="R$ 0,00"
        />

        {(item.codigos_oem?.length > 0 || item.codigos_fornecedores?.length > 0) && (
          <div className="mb-3 p-2 bg-[#1C1F24] rounded border border-[#3A3F48]">
            <p className="text-[10px] text-[#8B92A0] mb-1.5 font-semibold">Códigos verificáveis (read-only)</p>
            {item.codigos_oem?.length > 0 && (
              <p className="text-[10px] text-amber-400 mb-1"><strong>OEM:</strong> {item.codigos_oem.join(", ")}</p>
            )}
            {item.codigos_fornecedores?.length > 0 && (
              <p className="text-[10px] text-blue-400"><strong>Fornecedores:</strong> {item.codigos_fornecedores.join(", ")}</p>
            )}
          </div>
        )}
        
        <div className="flex gap-2">
          <button
            onClick={() => onDelete(item.id)}
            className="cp-focus px-4 py-2.5 rounded-lg border border-red-500/40 text-red-400 text-sm flex items-center gap-1.5"
          >
            <Trash2 size={14} /> Excluir
          </button>
          <button
            onClick={() => onSave(item.id, { nome, preco })}
            className="cp-focus flex-1 py-2.5 rounded-lg bg-amber-400 text-[#14161A] text-sm font-semibold"
          >
            Salvar
          </button>
        </div>
      </div>
    </div>
  );
}

function CatalogView({ items, loading, whatsapp, onEdit, onDelete }) {
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(null);

  const filtered = items.filter((it) => {
    const q = query.toLowerCase();
    if (!q) return true;
    return (
      it.nome?.toLowerCase().includes(q) ||
      it.categoria?.toLowerCase().includes(q) ||
      it.codigos_oem?.some((c) => c.toLowerCase().includes(q)) ||
      it.codigos_fornecedores?.some((c) => c.toLowerCase().includes(q))
    );
  });

  const waLink = (item) => {
    const numero = (whatsapp || "").replace(/\D/g, "");
    const msg = encodeURIComponent(
      `Olá! Tenho interesse em: ${item.nome}${item.codigos_oem_provaveis?.[0] ? " (cód. " + item.codigos_oem_provaveis[0] + ")" : ""}${item.preco ? " - " + item.preco : ""}`
    );
    return numero ? `https://wa.me/${numero}?text=${msg}` : null;
  };

  if (loading) {
    return (
      <div className="px-4 py-10 text-center text-[#8B92A0] text-sm">
        <Loader2 size={18} className="animate-spin mx-auto mb-2" />
        Carregando catálogo...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="px-4 py-14 text-center">
        <Package size={28} className="text-[#454B55] mx-auto mb-3" />
        <p className="text-[13px] text-[#8B92A0]">Nenhuma peça cadastrada ainda.</p>
        <p className="text-[12px] text-[#6B7280] mt-1">Vai em "Identificar" e tira a primeira foto.</p>
      </div>
    );
  }

  return (
    <div className="px-4 py-4 pb-24">
      <div className="relative mb-4">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6B7280]" />
        <input
          className="cp-focus w-full bg-[#1C1F24] border border-[#3A3F48] rounded-lg pl-9 pr-3 py-2.5 text-sm text-white"
          placeholder="Buscar por nome, categoria ou código..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        {filtered.map((item) => (
          <div key={item.id} className="cp-plate rounded-lg overflow-hidden">
            <div className="relative">
              <img src={item.foto} alt={item.nome} className="w-full h-28 object-cover" />
              <button
                onClick={() => setEditing(item)}
                className="cp-focus absolute top-1.5 right-1.5 w-7 h-7 rounded-full bg-black/60 flex items-center justify-center text-white"
                aria-label="Editar"
              >
                <Edit3 size={12} />
              </button>
            </div>
            <div className="p-2.5">
              <p className="text-[10px] cp-mono uppercase text-[#8B92A0] mb-0.5">{item.categoria}</p>
              <h3 className="text-[13px] font-semibold text-white leading-tight mb-1.5 line-clamp-2">{item.nome}</h3>
              {item.codigos_oem?.[0] && (
                <p className="cp-mono text-[10px] text-amber-400/90 mb-1.5 truncate">{item.codigos_oem[0]}</p>
              )}
              {item.origem && (
                <p className="text-[10px] text-[#6B7280] mb-1.5 truncate italic">{item.origem}</p>
              )}
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-bold text-white">{item.preco || "—"}</span>
                {waLink(item) ? (
                  <a
                    href={waLink(item)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="cp-focus w-7 h-7 rounded-full bg-green-500/15 flex items-center justify-center text-green-400"
                    aria-label="Chamar no WhatsApp"
                  >
                    <MessageCircle size={13} />
                  </a>
                ) : null}
              </div>
              <p className="text-[9px] text-[#6B7280] mt-1.5">{item.autor}</p>
            </div>
          </div>
        ))}
      </div>

      {editing && (
        <EditModal
          item={editing}
          onClose={() => setEditing(null)}
          onSave={(id, patch) => { onEdit(id, patch); setEditing(null); }}
          onDelete={(id) => { onDelete(id); setEditing(null); }}
        />
      )}
    </div>
  );
}

function VehicleSearchView({ memberName, setMemberName, onSaved }) {
  const [montadora, setMontadora] = useState("");
  const [modelo, setModelo] = useState("");
  const [ano, setAno] = useState("");
  const [motor, setMotor] = useState("");
  const [peca, setPeca] = useState("");
  const [status, setStatus] = useState("idle"); // idle | searching | done | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [preco, setPreco] = useState("");
  const [saving, setSaving] = useState(false);

  const buscar = async () => {
    if (!peca || !montadora || !modelo) {
      setErrorMsg("Preenche pelo menos: peça, montadora e modelo");
      return;
    }
    setStatus("searching");
    setResult(null);
    setErrorMsg("");
    try {
      const data = await searchByVehicle({
        peca: peca.trim(),
        montadora: montadora.trim(),
        modelo: modelo.trim(),
        ano: ano.trim() || undefined,
        motor: motor.trim() || undefined,
      });
      setResult(data);
      setStatus("done");
    } catch (err) {
      console.error(err);
      setErrorMsg("Não consegui achar informações dessa peça/veículo. Tenta revisar os dados.");
      setStatus("error");
    }
  };

  const reset = () => {
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
    setPreco("");
  };

  const salvar = async () => {
    if (!result) return;
    setSaving(true);
    try {
      let current = [];
      try {
        const existing = await window.storage.get(CATALOG_KEY, true);
        current = existing ? JSON.parse(existing.value) : [];
      } catch (_) {
        current = [];
      }
      const novoItem = {
        id: `item_${Date.now()}`,
        foto: null,
        preco: preco || null,
        autor: memberName || "sem nome",
        criadoEm: new Date().toISOString(),
        origem: `${montadora} ${modelo} ${ano || ""} ${motor || ""}`.trim(),
        ...result,
      };
      const atualizado = [novoItem, ...current];
      const saveResult = await window.storage.set(CATALOG_KEY, JSON.stringify(atualizado), true);
      if (!saveResult) throw new Error("Falha ao salvar");
      onSaved();
      reset();
      setPeca("");
      setMontadora("");
      setModelo("");
      setAno("");
      setMotor("");
    } catch (err) {
      console.error(err);
      setErrorMsg("Não consegui salvar no catálogo. Tenta de novo.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="px-4 py-5 pb-24">
      {!memberName && (
        <div className="cp-plate rounded-lg p-3 mb-4">
          <label className="text-[11px] text-[#8B92A0] block mb-1.5">Seu nome (aparece em quem cadastrou)</label>
          <input
            className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2 text-sm text-white"
            placeholder="ex: Fabio"
            onBlur={(e) => e.target.value && setMemberName(e.target.value)}
          />
        </div>
      )}

      {status === "idle" && (
        <div>
          <div className="cp-plate rounded-xl p-4 mb-3">
            <label className="text-[11px] text-[#8B92A0] block mb-1.5">Montadora</label>
            <input
              className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2.5 text-sm text-white"
              placeholder="ex: Volkswagen, Fiat, Ford, GM..."
              value={montadora}
              onChange={(e) => setMontadora(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="cp-plate rounded-xl p-4">
              <label className="text-[11px] text-[#8B92A0] block mb-1.5">Modelo</label>
              <input
                className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2.5 text-sm text-white"
                placeholder="ex: Gol, Uno, Fiesta"
                value={modelo}
                onChange={(e) => setModelo(e.target.value)}
              />
            </div>
            <div className="cp-plate rounded-xl p-4">
              <label className="text-[11px] text-[#8B92A0] block mb-1.5">Motor</label>
              <input
                className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2.5 text-sm text-white"
                placeholder="ex: 1.0, 1.6, 2.0"
                value={motor}
                onChange={(e) => setMotor(e.target.value)}
              />
            </div>
          </div>

          <div className="cp-plate rounded-xl p-4 mb-4">
            <label className="text-[11px] text-[#8B92A0] block mb-1.5">Ano / Período</label>
            <input
              className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2.5 text-sm text-white"
              placeholder="ex: 2010-2015 ou 2020"
              value={ano}
              onChange={(e) => setAno(e.target.value)}
            />
          </div>

          <div className="cp-plate rounded-xl p-4 mb-4">
            <label className="text-[11px] text-[#8B92A0] block mb-1.5">Peça que procura</label>
            <input
              className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2.5 text-sm text-white"
              placeholder="ex: válvula solenoide, sensor lambda, bomba combustível"
              value={peca}
              onChange={(e) => setPeca(e.target.value)}
            />
          </div>

          {errorMsg && <p className="text-[12px] text-red-400 mb-3">{errorMsg}</p>}

          <button
            onClick={buscar}
            className="cp-focus w-full py-3 rounded-lg bg-amber-400 hover:bg-amber-300 text-[#14161A] text-sm font-semibold flex items-center justify-center gap-2"
          >
            <Search size={15} />
            Buscar peça
          </button>
        </div>
      )}

      {status === "searching" && (
        <div className="cp-plate rounded-xl p-6 text-center relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-b from-amber-400/60 to-transparent cp-scanner cp-anim" />
          <div className="flex items-center justify-center gap-2 text-amber-300">
            <Loader2 size={16} className="animate-spin" />
            <span className="cp-mono text-[13px] cp-pulse cp-anim">pesquisando na web...</span>
          </div>
        </div>
      )}

      {status === "error" && (
        <div className="cp-plate rounded-xl p-6 text-center border-red-500/40">
          <AlertTriangle size={22} className="text-red-400 mx-auto mb-2" />
          <p className="text-[13px] text-[#C9CDD4] mb-4">{errorMsg}</p>
          <button onClick={reset} className="cp-focus text-sm text-amber-400 font-medium">
            Tentar de novo
          </button>
        </div>
      )}

      {status === "done" && result && (
        <div>
          <div className="mb-4">
            <span className="text-[11px] cp-mono uppercase tracking-wide text-[#8B92A0]">{result.categoria}</span>
            <span
              className={`ml-2 text-[10px] cp-mono uppercase px-2 py-0.5 rounded ${
                result.confianca === "alta"
                  ? "bg-green-500/15 text-green-400"
                  : result.confianca === "média"
                  ? "bg-amber-500/15 text-amber-400"
                  : "bg-red-500/15 text-red-400"
              }`}
            >
              confiança {result.confianca}
            </span>
          </div>
          <h2 className="cp-display text-xl text-white mb-3">{result.nome}</h2>

          <p className="text-[12px] text-[#8B92A0] mb-3 italic">
            Busca de: {montadora} {modelo} {ano && `(${ano})`} {motor && `- Motor ${motor}`}
          </p>

          {result.codigos_oem?.length > 0 && (
            <div className="mb-3">
              <p className="text-[11px] text-[#8B92A0] mb-1.5 font-semibold">Códigos OEM (Montadora)</p>
              <div className="flex flex-wrap">
                {result.codigos_oem.map((c, i) => <Chip key={i}>{c}</Chip>)}
              </div>
            </div>
          )}

          {result.codigos_fornecedores?.length > 0 && (
            <div className="mb-3">
              <p className="text-[11px] text-[#8B92A0] mb-1.5 font-semibold">Códigos de Fornecedores</p>
              <div className="flex flex-wrap">
                {result.codigos_fornecedores.map((s, i) => (
                  <span key={i} className="cp-plate cp-mono inline-block px-2 py-1 text-[11px] rounded text-blue-300 mr-1.5 mb-1.5">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.preco_referencia && (
            <div className="mb-3 p-2 bg-green-500/10 rounded border border-green-500/30">
              <p className="text-[11px] text-[#8B92A0] mb-0.5">Preço de referência</p>
              <p className="text-[14px] font-bold text-green-400">{result.preco_referencia}</p>
            </div>
          )}

          {result.aplicacoes_provaveis?.length > 0 && (
            <div className="mb-3">
              <p className="text-[11px] text-[#8B92A0] mb-1.5">Aplicações confirmadas</p>
              <ul className="text-[13px] text-[#C9CDD4] space-y-1">
                {result.aplicacoes_provaveis.map((a, i) => (
                  <li key={i}>• {a}</li>
                ))}
              </ul>
            </div>
          )}

          {result.observacoes && (
            <div className="mb-4">
              <p className="text-[11px] text-[#8B92A0] mb-1">Observações</p>
              <p className="text-[13px] text-[#C9CDD4] leading-relaxed">{result.observacoes}</p>
            </div>
          )}

          <p className="text-[11px] text-[#6B7280] mb-4 italic">
            Essa busca consultou a web pra confirmar os dados — é mais confiável que só foto, mas sempre confira o código antes de vender.
          </p>

          <div className="mb-4">
            <label className="text-[11px] text-[#8B92A0] block mb-1.5">Preço (opcional)</label>
            <input
              className="cp-focus w-full bg-[#1C1F24] border border-[#3A3F48] rounded-lg px-3 py-2.5 text-sm text-white"
              placeholder="R$ 0,00"
              value={preco}
              onChange={(e) => setPreco(e.target.value)}
            />
          </div>

          <div className="flex gap-2">
            <button onClick={reset} className="cp-focus flex-1 py-3 rounded-lg border border-[#3A3F48] text-[#C9CDD4] text-sm font-medium">
              Descartar
            </button>
            <button
              onClick={salvar}
              disabled={saving}
              className="cp-focus flex-[2] py-3 rounded-lg bg-amber-400 hover:bg-amber-300 disabled:opacity-60 text-[#14161A] text-sm font-semibold flex items-center justify-center gap-2"
            >
              {saving ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />}
              Adicionar ao catálogo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ConfigView({ whatsapp, setWhatsapp, memberName, setMemberName }) {
  const [localWa, setLocalWa] = useState(whatsapp || "");
  const [localName, setLocalName] = useState(memberName || "");
  const [saved, setSaved] = useState(false);

  const salvar = async () => {
    try {
      await window.storage.set(CONFIG_KEY, JSON.stringify({ whatsapp: localWa }), true);
      await window.storage.set(MEMBER_KEY, localName, false);
      setWhatsapp(localWa);
      setMemberName(localName);
      setSaved(true);
      setTimeout(() => setSaved(false), 1800);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="px-4 py-5 pb-24">
      <div className="cp-plate rounded-xl p-4 mb-4">
        <h3 className="cp-display text-white text-sm mb-1">WhatsApp da loja</h3>
        <p className="text-[12px] text-[#8B92A0] mb-3">Usado no botão de contato de cada peça. Formato: DDI + DDD + número.</p>
        <input
          className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2.5 text-sm text-white"
          placeholder="5511999999999"
          value={localWa}
          onChange={(e) => setLocalWa(e.target.value)}
        />
      </div>

      <div className="cp-plate rounded-xl p-4 mb-4">
        <h3 className="cp-display text-white text-sm mb-1">Seu nome</h3>
        <p className="text-[12px] text-[#8B92A0] mb-3">Aparece nas peças que você cadastrar. Cada pessoa da equipe define o próprio nome no aparelho dela.</p>
        <input
          className="cp-focus w-full bg-[#14161A] border border-[#3A3F48] rounded px-3 py-2.5 text-sm text-white"
          placeholder="ex: Fabio"
          value={localName}
          onChange={(e) => setLocalName(e.target.value)}
        />
      </div>

      <button onClick={salvar} className="cp-focus w-full py-3 rounded-lg bg-amber-400 text-[#14161A] text-sm font-semibold flex items-center justify-center gap-2">
        {saved ? <Check size={15} /> : null}
        {saved ? "Salvo" : "Salvar configurações"}
      </button>

      <p className="text-[11px] text-[#6B7280] mt-5 leading-relaxed">
        Nota: o número de WhatsApp e o catálogo ficam visíveis pra qualquer pessoa que use este app (dado compartilhado). O nome fica só no seu aparelho.
      </p>
    </div>
  );
}

export default function CatalogoPecasApp() {
  const [view, setView] = useState("capture");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [whatsapp, setWhatsapp] = useState("");
  const [memberName, setMemberName] = useState("");

  const loadCatalog = async () => {
    try {
      const res = await window.storage.get(CATALOG_KEY, true);
      setItems(res ? JSON.parse(res.value) : []);
    } catch (_) {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCatalog();
    (async () => {
      try {
        const cfg = await window.storage.get(CONFIG_KEY, true);
        if (cfg) setWhatsapp(JSON.parse(cfg.value).whatsapp || "");
      } catch (_) {}
      try {
        const name = await window.storage.get(MEMBER_KEY, false);
        if (name) setMemberName(name.value || "");
      } catch (_) {}
    })();
  }, []);

  const handleEdit = async (id, patch) => {
    const updated = items.map((it) => (it.id === id ? { ...it, ...patch } : it));
    setItems(updated);
    try {
      await window.storage.set(CATALOG_KEY, JSON.stringify(updated), true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    const updated = items.filter((it) => it.id !== id);
    setItems(updated);
    try {
      await window.storage.set(CATALOG_KEY, JSON.stringify(updated), true);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="cp-root min-h-screen bg-[#14161A]">
      <style>{FONT_STYLE}</style>
      <Header view={view} setView={setView} itemCount={items.length} />
      {view === "capture" && (
        <CaptureView memberName={memberName} setMemberName={setMemberName} onSaved={loadCatalog} />
      )}
      {view === "vehicle" && (
        <VehicleSearchView memberName={memberName} setMemberName={setMemberName} onSaved={loadCatalog} />
      )}
      {view === "catalog" && (
        <CatalogView items={items} loading={loading} whatsapp={whatsapp} onEdit={handleEdit} onDelete={handleDelete} />
      )}
      {view === "config" && (
        <ConfigView whatsapp={whatsapp} setWhatsapp={setWhatsapp} memberName={memberName} setMemberName={setMemberName} />
      )}
    </div>
  );
}
