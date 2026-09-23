import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

class ApiService {
  static const _storage = FlutterSecureStorage();
  static const _keyToken = 'qrqc_token';
  static const _keyBaseUrl = 'qrqc_base_url';
  static const _defaultUrl = 'http://127.0.0.1:5000';

  String _baseUrl = _defaultUrl;
  String? _token;

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_keyBaseUrl) ?? _defaultUrl;
    _token = await _storage.read(key: _keyToken);
  }

  String get baseUrl => _baseUrl;
  bool get isAuthenticated => _token != null;

  Future<void> setBaseUrl(String url) async {
    _baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyBaseUrl, _baseUrl);
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Future<Usuario> login(String username, String password) async {
    final resp = await http
        .post(
          Uri.parse('$_baseUrl/api/mobile/login'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'username': username, 'password': password}),
        )
        .timeout(const Duration(seconds: 15));

    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw body['erro'] as String? ?? 'Erro ao fazer login';
    }
    _token = body['token'] as String;
    await _storage.write(key: _keyToken, value: _token);
    return Usuario.fromJson(body, _token!);
  }

  Future<void> logout() async {
    _token = null;
    await _storage.delete(key: _keyToken);
  }

  Future<List<Maquina>> getMaquinas() async {
    final resp = await http.get(
      Uri.parse('$_baseUrl/api/mobile/maquinas'),
      headers: _headers,
    ).timeout(const Duration(seconds: 10));
    _checkAuth(resp);
    final list = jsonDecode(resp.body) as List;
    return list.map((e) => Maquina.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Ocorrencia>> getOcorrencias({int limit = 30}) async {
    final resp = await http.get(
      Uri.parse('$_baseUrl/api/mobile/ocorrencias?limit=$limit'),
      headers: _headers,
    ).timeout(const Duration(seconds: 10));
    _checkAuth(resp);
    final list = jsonDecode(resp.body) as List;
    return list
        .map((e) => Ocorrencia.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> criarOcorrencia(Map<String, dynamic> data) async {
    final resp = await http
        .post(
          Uri.parse('$_baseUrl/api/mobile/ocorrencias'),
          headers: _headers,
          body: jsonEncode(data),
        )
        .timeout(const Duration(seconds: 15));
    _checkAuth(resp);
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<ResultadoSensor> analisarEquipamento(
    File foto, {
    String contexto = '',
    int? maquinaId,
  }) async {
    final req = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/api/sensor/analisar'),
    );
    req.headers['Authorization'] = 'Bearer $_token';
    req.files.add(await http.MultipartFile.fromPath('foto', foto.path));
    req.fields['contexto'] = contexto;
    if (maquinaId != null) req.fields['maquina_id'] = maquinaId.toString();

    final streamed = await req.send().timeout(const Duration(seconds: 60));
    final body = await http.Response.fromStream(streamed);
    if (body.statusCode == 401) throw 'Sessão expirada. Faça login novamente.';
    final json = jsonDecode(body.body) as Map<String, dynamic>;
    if (json['erro'] != null) throw json['erro'] as String;
    return ResultadoSensor.fromJson(json);
  }

  Future<ResultadoDocumento> analisarDocumento(
    File foto, {
    String tipoDocumento = '',
  }) async {
    final req = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/api/mobile/inspecao/documento'),
    );
    req.headers['Authorization'] = 'Bearer $_token';
    req.files.add(await http.MultipartFile.fromPath('foto', foto.path));
    req.fields['tipo_documento'] = tipoDocumento;

    final streamed = await req.send().timeout(const Duration(seconds: 60));
    final body = await http.Response.fromStream(streamed);
    if (body.statusCode == 401) throw 'Sessão expirada. Faça login novamente.';
    final json = jsonDecode(body.body) as Map<String, dynamic>;
    if (json['erro'] != null) throw json['erro'] as String;
    return ResultadoDocumento.fromJson(json);
  }

  void _checkAuth(http.Response resp) {
    if (resp.statusCode == 401) {
      _token = null;
      throw 'Sessão expirada. Faça login novamente.';
    }
    if (resp.statusCode >= 400) {
      final body = jsonDecode(resp.body) as Map<String, dynamic>?;
      throw body?['erro'] as String? ?? 'Erro ${resp.statusCode}';
    }
  }
}
