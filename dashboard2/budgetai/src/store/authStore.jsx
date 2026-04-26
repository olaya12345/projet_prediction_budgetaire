    import { create } from "zustand";

    const initialToken = localStorage.getItem("budgetai_token");
    const initialUser = localStorage.getItem("budgetai_user");

    const useAuthStore = create((set) => ({
    token: initialToken || null,
    user: initialUser ? JSON.parse(initialUser) : null,
    setAuth: ({ token, user }) =>
        set(() => {
        localStorage.setItem("budgetai_token", token);
        localStorage.setItem("budgetai_user", JSON.stringify(user));
        return { token, user };
        }),
    logout: () =>
        set(() => {
        localStorage.removeItem("budgetai_token");
        localStorage.removeItem("budgetai_user");
        return { token: null, user: null };
        }),
    }));

    export default useAuthStore;
