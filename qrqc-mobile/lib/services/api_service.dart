import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

/// Erro já em linguagem de usuário: a tela mostra [mensagem] como está.
class ApiException implements Exception {
  final String mensagem;
  const ApiException(this.mensagem);
  @override
  String toString() => mensagem;
}

class ApiService {
  static const _storage = FlutterSecureStorage();
  static const _keyToken = 'qrqc_token';
  static const _keyBaseUrl = 'qrqc_base_url';
  // Servidor publicado. Na rede local (desenvolvimento) troque em "Alterar servidor".
  static const servidorPadrao = 'https://nexar-qrqc-production.up.railway.app';

  /// Chamado quando o servidor recusa o token (sessão expirada ou revogada):
  /// o app registra em main.dart a volta para o login.
  static void Function()? onSessaoExpirada;

  String _baseUrl = servidorPadrao;
  String? _token;

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final salvo = prefs.getString(_keyBaseUrl);
    // Versões antigas gravavam o padrão http://127.0.0.1:5000, que nunca funciona no celular
    _baseUrl = (salvo == null || salvo == 'http://127.0.0.1:5000') ? servidorPadrao : salvo;
    try {
      _token = await _storage.read(key: _keyToken).timeout(
        const Duration(seconds: 4),
        onTimeout: () => null,
      );
    } catch (_) {
      _token = null;
    }
  }

  String get baseUrl => _baseUrl;
  bool get isAuthenticated => _token != null;

  Future<void> setBaseUrl(String url) async {
    var u = url.trim();
    if (u.isNotEmpty && !u.startsWith('http')) u = 'https://$u';
    _baseUrl = u.endsWith('/') ? u.substring(0, u.length - 1) : u;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyBaseUrl, _baseUrl);
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Uri _url(String caminho) => Uri.parse('$_baseUrl$caminho');

  // ── Requisição com tratamento único de erro ────────────────────────────
  /// Executa [fazer], traduz falhas de rede e respostas de erro para [ApiException]
  /// e trata o 401 (exceto no login, onde 401 é senha errada).
  Future<http.Response> _enviar(
    Future<http.Response> Function() fazer, {
    Duration limite = const Duration(seconds: 15),
    bool autenticado = true,
  }) async {
    final http.Response resp;
    try {
      resp = await fazer().timeout(limite);
    } on TimeoutException {
      throw const ApiException('O servidor demorou para responder. Tente novamente.');
    } on SocketException {
      throw const ApiException('Sem conexão com o servidor. Verifique o Wi-Fi ou os dados móveis.');
    } on HandshakeException {
      throw const ApiException('Não foi possível abrir uma conexão segura com o servidor.');
    } on http.ClientException {
      throw const ApiException('A conexão com o servidor caiu. Tente novamente.');
    }
    if (resp.statusCode == 401 && autenticado) {
      await _descartarSessao();
      onSessaoExpirada?.call();
      throw const ApiException('Sua sessão expirou. Entre novamente.');
    }
    if (resp.statusCode >= 400) {
      throw ApiException(_mensagemDeErro(resp));
    }
    return resp;
  }

  String _mensagemDeErro(http.Response resp) {
    try {
      final corpo = jsonDecode(utf8.decode(resp.bodyBytes));
      if (corpo is Map && corpo['erro'] is String) return corpo['erro'] as String;
    } catch (_) {}
    return switch (resp.statusCode) {
      413 => 'A foto é grande demais para enviar.',
      429 => 'Muitas tentativas seguidas. Aguarde um minuto e tente de novo.',
      >= 500 => 'O servidor está com problemas agora (erro ${resp.statusCode}). Tente em instantes.',
      _ => 'Não foi possível concluir (erro ${resp.statusCode}).',
    };
  }

  dynamic _json(http.Response resp) {
    try {
      return jsonDecode(utf8.decode(resp.bodyBytes));
    } on FormatException {
      throw const ApiException('Resposta inesperada do servidor. Confira o endereço do servidor.');
    }
  }

  Future<void> _descartarSessao() async {
    _token = null;
    await _storage.delete(key: _keyToken);
  }

  // ── Sessão ─────────────────────────────────────────────────────────────
  Future<Usuario> login(String username, String password) async {
    final resp = await _enviar(
      () => http.post(_url('/api/mobile/login'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'username': username, 'password': password})),
      autenticado: false,
    );
    final body = _json(resp) as Map<String, dynamic>;
    _token = body['token'] as String;
    await _storage.write(key: _keyToken, value: _token);
    return Usuario.fromJson(body, _token!);
  }

  Future<void> logout() async {
    // Revoga o token no servidor (melhor esforço: sem rede, apaga só localmente)
    if (_token != null) {
      try {
        await http
            .post(_url('/api/mobile/logout'), headers: _headers)
            .timeout(const Duration(seconds: 5));
      } catch (_) {}
    }
    await _descartarSessao();
  }

  // ── Máquinas e ocorrências ─────────────────────────────────────────────
  Future<List<Maquina>> getMaquinas() async {
    final resp = await _enviar(() => http.get(_url('/api/mobile/maquinas'), headers: _headers));
    return (_json(resp) as List)
        .map((e) => Maquina.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Componente>> getComponentes(int maquinaId) async {
    final resp = await _enviar(
        () => http.get(_url('/api/mobile/maquinas/$maquinaId/componentes'), headers: _headers));
    return (_json(resp) as List)
        .map((e) => Componente.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Sintoma>> getSintomas(int maquinaId, String componenteId) async {
    final resp = await _enviar(() => http.get(
        _url('/api/mobile/maquinas/$maquinaId/componentes/${Uri.encodeComponent(componenteId)}/sintomas'),
        headers: _headers));
    final body = _json(resp) as Map<String, dynamic>;
    return (body['sintomas'] as List? ?? [])
        .map((e) => Sintoma.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Ocorrencia>> getOcorrencias({int limit = 30}) async {
    final resp = await _enviar(
        () => http.get(_url('/api/mobile/ocorrencias?limit=$limit'), headers: _headers));
    return (_json(resp) as List)
        .map((e) => Ocorrencia.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<int> criarOcorrencia(Map<String, dynamic> data) async {
    final resp = await _enviar(() => http.post(_url('/api/mobile/ocorrencias'),
        headers: _headers, body: jsonEncode(data)));
    return (_json(resp) as Map<String, dynamic>)['id'] as int;
  }

  // ── Sensor Visual e documentos ─────────────────────────────────────────
  Future<http.Response> _enviarFoto(String caminho, File foto, Map<String, String> campos) {
    // A IA leva de 15 a 30 s; o limite cobre a troca para o modelo reserva
    return _enviar(() async {
      final req = http.MultipartRequest('POST', _url(caminho));
      req.headers['Authorization'] = 'Bearer $_token';
      req.files.add(await http.MultipartFile.fromPath('foto', foto.path));
      req.fields.addAll(campos);
      return http.Response.fromStream(await req.send());
    }, limite: const Duration(seconds: 90));
  }

  Future<ResultadoSensor> analisarEquipamento(File foto, {String contexto = '', int? maquinaId}) async {
    final resp = await _enviarFoto('/api/mobile/sensor/analisar', foto, {
      'contexto': contexto,
      if (maquinaId != null) 'maquina_id': maquinaId.toString(),
    });
    return ResultadoSensor.fromJson(_json(resp) as Map<String, dynamic>);
  }

  Future<ResultadoDocumento> analisarDocumento(File foto, {String tipoDocumento = ''}) async {
    final resp = await _enviarFoto('/api/mobile/inspecao/documento', foto, {
      'tipo_documento': tipoDocumento,
    });
    return ResultadoDocumento.fromJson(_json(resp) as Map<String, dynamic>);
  }

  Future<void> validarInspecao(int inspecaoId) async {
    await _enviar(() => http.post(_url('/api/mobile/sensor/$inspecaoId/confirmar'),
        headers: _headers, body: '{}'));
  }

  /// PDF do laudo da inspeção (bytes), para compartilhar.
  Future<Uint8List> baixarLaudo(int inspecaoId) async {
    final resp = await _enviar(
        () => http.get(_url('/api/mobile/sensor/$inspecaoId/laudo.pdf'), headers: _headers),
        limite: const Duration(seconds: 45));
    return resp.bodyBytes;
  }
}
