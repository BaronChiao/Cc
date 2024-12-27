import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const VIPScreen = () => {
  const [vipLevels, setVipLevels] = useState([]);
  const [currentVIP, setCurrentVIP] = useState(null);

  useEffect(() => {
    loadVIPLevels();
    loadCurrentVIP();
  }, []);

  const loadVIPLevels = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const response = await fetch('YOUR_SERVER_URL/api/vip/levels', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setVipLevels(data);
    } catch (error) {
      Alert.alert('错误', '加载VIP等级失败');
    }
  };

  const loadCurrentVIP = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const response = await fetch('YOUR_SERVER_URL/api/user/profile', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setCurrentVIP(data.vip_level);
    } catch (error) {
      Alert.alert('错误', '加载用户信息失败');
    }
  };

  const purchaseVIP = async (levelId) => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const response = await fetch('YOUR_SERVER_URL/api/vip/purchase', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ level_id: levelId })
      });
      const data = await response.json();
      Alert.alert('成功', data.message);
      loadCurrentVIP();
    } catch (error) {
      Alert.alert('错误', '购买VIP失败');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>VIP会员</Text>
      <FlatList
        data={vipLevels}
        renderItem={({ item }) => (
          <View style={styles.vipCard}>
            <Text style={styles.vipName}>{item.name}</Text>
            <Text style={styles.vipPrice}>¥{item.price}/月</Text>
            <Text style={styles.vipFeature}>
              可创建{item.max_private_circles}个私密圈子
            </Text>
            <TouchableOpacity
              style={[
                styles.purchaseButton,
                currentVIP === item.id && styles.currentVIP
              ]}
              onPress={() => purchaseVIP(item.id)}
              disabled={currentVIP === item.id}
            >
              <Text style={styles.buttonText}>
                {currentVIP === item.id ? '当前等级' : '立即购买'}
              </Text>
            </TouchableOpacity>
          </View>
        )}
        keyExtractor={item => item.id.toString()}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 15,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  vipCard: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    marginBottom: 15,
    elevation: 2,
  },
  vipName: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  vipPrice: {
    fontSize: 18,
    color: '#FF6B6B',
    marginBottom: 10,
  },
  vipFeature: {
    fontSize: 16,
    color: '#666',
    marginBottom: 15,
  },
  purchaseButton: {
    backgroundColor: '#007AFF',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  currentVIP: {
    backgroundColor: '#4CD964',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default VIPScreen; 