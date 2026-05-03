import 'package:susanoo/services/api_service.dart';

class ChatMessage {
  final String id;
  final String senderType; // user | bot | agent
  final String content;
  final List<String> suggestedActions;
  final bool shouldEscalate;
  final String? agentUsed;
  final String? language;
  final DateTime createdAt;

  ChatMessage({
    required this.id,
    required this.senderType,
    required this.content,
    required this.suggestedActions,
    required this.shouldEscalate,
    this.agentUsed,
    this.language,
    required this.createdAt,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> j) => ChatMessage(
        id: j['id'] ?? '',
        senderType: j['sender_type'] ?? 'bot',
        content: j['content'] ?? '',
        suggestedActions: List<String>.from(j['suggested_actions'] ?? []),
        shouldEscalate: j['should_escalate'] ?? false,
        agentUsed: j['agent_used'],
        language: j['language'],
        createdAt: DateTime.tryParse(j['created_at'] ?? '') ?? DateTime.now(),
      );

  bool get isUser => senderType == 'user';
}

class ChatResponse {
  final String messageId;
  final String conversationId;
  final String answer;
  final String intent;
  final bool shouldEscalate;
  final String? escalationReason;
  final List<String> suggestedActions;
  final double confidence;
  final String agentUsed;
  final String language;

  ChatResponse({
    required this.messageId,
    required this.conversationId,
    required this.answer,
    required this.intent,
    required this.shouldEscalate,
    this.escalationReason,
    required this.suggestedActions,
    required this.confidence,
    required this.agentUsed,
    required this.language,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> j) => ChatResponse(
        messageId: j['message_id'] ?? '',
        conversationId: j['conversation_id'] ?? '',
        answer: j['answer'] ?? '',
        intent: j['intent'] ?? 'general',
        shouldEscalate: j['should_escalate'] ?? false,
        escalationReason: j['escalation_reason'],
        suggestedActions: List<String>.from(j['suggested_actions'] ?? []),
        confidence: (j['confidence'] ?? 0.0).toDouble(),
        agentUsed: j['agent_used'] ?? 'unknown',
        language: j['language'] ?? 'en',
      );
}

class ChatService {
  final ApiService _api;
  ChatService(this._api);

  Future<ChatResponse> sendMessage(String message,
      {String? conversationId}) async {
    final res = await _api.sendChatMessage(message,
        conversationId: conversationId);
    return ChatResponse.fromJson(res);
  }

  Future<List<ChatMessage>> getHistory() async {
    final list = await _api.getChatHistory();
    return list.map((e) => ChatMessage.fromJson(e)).toList();
  }

  Future<void> sendFeedback(String messageId, int rating,
      {String? comment}) async {
    await _api.sendChatFeedback(messageId, rating, comment: comment);
  }
}
