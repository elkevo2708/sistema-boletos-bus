import { useEffect, useState } from 'react';
import { enviarFormulario } from '../api';

const TIPOS = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const TOPE = 5 * 1024 * 1024;
const ACEPTA = 'image/jpeg,image/png,image/webp,image/gif,.jpg,.jpeg,.png,.webp,.gif';

function tipoValido(archivo) {
  if (TIPOS.includes(archivo.type)) return true;
  return /\.(jpe?g|png|webp|gif)$/i.test(archivo.name || '');
}

export default function CampoImagen({ token, valor, onChange, etiqueta = 'Imagen', onSubiendo }) {
  const [local, setLocal] = useState('');
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
  const [subiendo, setSubiendo] = useState(false);

  useEffect(() => () => {
    if (local) URL.revokeObjectURL(local);
  }, [local]);

  function marcar(activo) {
    setSubiendo(activo);
    if (onSubiendo) onSubiendo(activo);
  }

  async function elegir(event) {
    const archivo = event.target.files?.[0];
    event.target.value = '';
    if (!archivo) return;
    setError('');
    setAviso('');
    if (!tipoValido(archivo)) {
      setError('Use una imagen JPG, PNG, WebP o GIF.');
      return;
    }
    if (!archivo.size || archivo.size > TOPE) {
      setError('La imagen debe pesar entre 1 byte y 5 MB.');
      return;
    }
    if (local) URL.revokeObjectURL(local);
    const previaLocal = URL.createObjectURL(archivo);
    setLocal(previaLocal);
    const datos = new FormData();
    datos.set('archivo', archivo);
    marcar(true);
    try {
      const respuesta = await enviarFormulario('/admin/imagenes', { token, datos });
      URL.revokeObjectURL(previaLocal);
      setLocal('');
      onChange(respuesta.url);
      setAviso(`Imagen lista: ${archivo.name}`);
    } catch (err) {
      setError(err.message);
      setAviso('');
    } finally {
      marcar(false);
    }
  }

  function escribir(texto) {
    setAviso('');
    setError('');
    if (local) {
      URL.revokeObjectURL(local);
      setLocal('');
    }
    onChange(texto);
  }

  const previa = local || valor;

  return (
    <div className="campo-imagen">
      <p className="campo-imagen-etiqueta">{etiqueta}</p>
      {previa ? (
        <img className="campo-imagen-previa" src={previa} alt="Vista previa de la imagen" />
      ) : (
        <p className="meta">La vista previa aparece al elegir un archivo o al pegar una URL.</p>
      )}
      <div className="campo-imagen-botones">
        <label>
          Galería
          <input
            type="file"
            accept={ACEPTA}
            aria-label={`${etiqueta}: elegir de la galería`}
            disabled={subiendo}
            onChange={elegir}
          />
        </label>
        <label>
          Cámara
          <input
            type="file"
            accept={ACEPTA}
            capture="environment"
            aria-label={`${etiqueta}: tomar foto`}
            disabled={subiendo}
            onChange={elegir}
          />
        </label>
      </div>
      <p className="meta">En el celular, Galería abre las fotos y Cámara abre la cámara. JPG, PNG, WebP o GIF, hasta 5 MB.</p>
      {subiendo && <p className="meta" role="status">Subiendo imagen…</p>}
      {aviso && !subiendo && <p className="aviso-ok" role="status">{aviso}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}
      <label>
        O pegue una URL
        <input
          value={valor || ''}
          onChange={(e) => escribir(e.target.value)}
          placeholder="https://… o /turismo/foto.jpg"
          aria-label={`${etiqueta}: URL`}
          disabled={subiendo}
        />
      </label>
    </div>
  );
}
