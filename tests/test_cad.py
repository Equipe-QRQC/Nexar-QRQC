"""Importação de CAD: zip seguro e acentos dos nomes das peças (sem precisar do conversor)."""
import io
import zipfile

import pytest

import cad_import


def test_zip_bomba_e_recusado(tmp_path, monkeypatch):
    monkeypatch.setattr(cad_import, "MAX_DESCOMPACTADO", 1024 * 1024)
    zb = tmp_path / "b.zip"
    with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("a/peca.step", b"0" * (3 * 1024 * 1024))
    with pytest.raises(ValueError, match="3 GB"):
        cad_import.extrair_steps(str(zb), str(tmp_path))


def test_nomes_repetidos_em_pastas_diferentes_nao_se_sobrescrevem(tmp_path):
    zd = tmp_path / "d.zip"
    with zipfile.ZipFile(zd, "w") as z:
        z.writestr("a/peca.step", b"A")
        z.writestr("b/peca.step", b"B")
    arquivos = cad_import.extrair_steps(str(zd), str(tmp_path))
    assert len(arquivos) == 2 and {open(a).read() for a in arquivos} == {"A", "B"}


def test_acento_latin1_do_step_vira_escape_da_norma():
    pytest.importorskip("OCP", reason="conversor de CAD opcional (requirements-cad.txt)")
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location("cad_para_glb", pathlib.Path("scripts/cad_para_glb.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert mod._texto_step(b"#1=PRODUCT('CAIXA EL\xc9TRICA','','');") == b"#1=PRODUCT('CAIXA EL\\X2\\00C9\\X0\\TRICA','','');"


def test_salvar_cad_com_rotacao_invalida_da_400(admin, db):
    job = db.execute("INSERT INTO importacoes_cad (slug, nome, arquivo, status) VALUES ('teste-cad', 'T', 'a.step', 'mapear')").lastrowid
    db.commit()
    comps = [{"id": "a", "nome": "A", "nos": ["A*"]}, {"id": "b", "nome": "B", "nos": ["B*"]}]
    r = admin.post(f"/api/cad/{job}/salvar", json={"componentes": comps, "rotacao": [0, "noventa", 0]})
    assert r.status_code == 400
