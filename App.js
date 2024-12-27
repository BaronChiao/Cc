import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import LoginScreen from './LoginScreen';
import ChatScreen from './ChatScreen';
import FriendListScreen from './FriendListScreen';
import VIPScreen from './VIPScreen';
import CircleScreen from './CircleScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const MainTabs = () => {
  return (
    <Tab.Navigator>
      <Tab.Screen 
        name="Chat" 
        component={ChatScreen} 
        options={{ title: '聊天' }}
      />
      <Tab.Screen 
        name="Friends" 
        component={FriendListScreen} 
        options={{ title: '好友' }}
      />
      <Tab.Screen 
        name="Circles" 
        component={CircleScreen} 
        options={{ title: '圈子' }}
      />
      <Tab.Screen 
        name="VIP" 
        component={VIPScreen} 
        options={{ title: 'VIP' }}
      />
    </Tab.Navigator>
  );
};

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen 
          name="Login" 
          component={LoginScreen} 
          options={{ headerShown: false }}
        />
        <Stack.Screen 
          name="Main" 
          component={MainTabs}
          options={{ headerShown: false }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
} 