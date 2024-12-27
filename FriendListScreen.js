import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const FriendListScreen = ({ navigation }) => {
  const [friends, setFriends] = useState([]);
  const [requests, setRequests] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  useEffect(() => {
    loadFriends();
    loadFriendRequests();
  }, []);

  const loadFriends = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const response = await fetch('YOUR_SERVER_URL/api/friends', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setFriends(data);
    } catch (error) {
      Alert.alert('错误', '加载好友列表失败');
    }
  };

  const loadFriendRequests = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const response = await fetch('YOUR_SERVER_URL/api/friends/requests', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setRequests(data);
    } catch (error) {
      Alert.alert('错误', '加载好友请求失败');
    }
  };

  const searchUsers = async () => {
    if (!searchQuery.trim()) return;
    try {
      const token = await AsyncStorage.getItem('userToken');
      const response = await fetch(`YOUR_SERVER_URL/api/friends/search?query=${searchQuery}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      Alert.alert('错误', '搜索用户失败');
    }
  };

  const sendFriendRequest = async (friendId) => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const response = await fetch('YOUR_SERVER_URL/api/friends/request', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ friend_id: friendId })
      });
      const data = await response.json();
      Alert.alert('成功', data.message);
      setSearchResults([]);
      setSearchQuery('');
    } catch (error) {
      Alert.alert('错误', '发送好友请求失败');
    }
  };

  const respondToRequest = async (requestId, response) => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      await fetch('YOUR_SERVER_URL/api/friends/respond', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ request_id: requestId, response })
      });
      loadFriendRequests();
      loadFriends();
    } catch (error) {
      Alert.alert('错误', '处理好友请求失败');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder="搜索用户..."
          onSubmitEditing={searchUsers}
        />
      </View>

      {searchResults.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>搜索结果</Text>
          <FlatList
            data={searchResults}
            renderItem={({ item }) => (
              <View style={styles.userItem}>
                <Text>{item.username}</Text>
                <TouchableOpacity
                  style={styles.addButton}
                  onPress={() => sendFriendRequest(item.id)}
                >
                  <Text style={styles.buttonText}>添加</Text>
                </TouchableOpacity>
              </View>
            )}
            keyExtractor={item => item.id.toString()}
          />
        </View>
      )}

      {requests.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>好友请求</Text>
          <FlatList
            data={requests}
            renderItem={({ item }) => (
              <View style={styles.requestItem}>
                <Text>{item.username}</Text>
                <View style={styles.requestButtons}>
                  <TouchableOpacity
                    style={[styles.responseButton, styles.acceptButton]}
                    onPress={() => respondToRequest(item.id, 'accept')}
                  >
                    <Text style={styles.buttonText}>接受</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.responseButton, styles.rejectButton]}
                    onPress={() => respondToRequest(item.id, 'reject')}
                  >
                    <Text style={styles.buttonText}>拒绝</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
            keyExtractor={item => item.id.toString()}
          />
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>好友列表</Text>
        <FlatList
          data={friends}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.friendItem}
              onPress={() => navigation.navigate('Chat', { friendId: item.id })}
            >
              <Text>{item.username}</Text>
            </TouchableOpacity>
          )}
          keyExtractor={item => item.id.toString()}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  searchContainer: {
    padding: 10,
    backgroundColor: '#fff',
  },
  searchInput: {
    backgroundColor: '#f0f0f0',
    padding: 10,
    borderRadius: 8,
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    padding: 10,
  },
  userItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  requestItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  friendItem: {
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  addButton: {
    backgroundColor: '#007AFF',
    padding: 8,
    borderRadius: 5,
  },
  requestButtons: {
    flexDirection: 'row',
  },
  responseButton: {
    padding: 8,
    borderRadius: 5,
    marginLeft: 10,
  },
  acceptButton: {
    backgroundColor: '#4CD964',
  },
  rejectButton: {
    backgroundColor: '#FF3B30',
  },
  buttonText: {
    color: '#fff',
  },
});

export default FriendListScreen; 