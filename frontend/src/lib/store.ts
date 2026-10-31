import {create} from 'zustand'
import type {Island, User} from './api'

type State = {user: User | null; island: Island | null; setUser: (user: User | null) => void;
  setIsland: (island: Island | null) => void; logout: () => void}

export const useApp = create<State>((set) => ({
  user: null, island: null,
  setUser: (user) => set({user}), setIsland: (island) => set({island}),
  logout: () => {localStorage.removeItem('island-token'); set({user: null, island: null})},
}))
