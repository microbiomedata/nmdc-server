import { InjectionKey, inject, provide } from 'vue';
import VueRouter from 'vue-router';

const routerKey: InjectionKey<VueRouter> = Symbol('router');

export function provideRouter(router: VueRouter): void {
  provide(routerKey, router);
}

export function useRouter(): void | VueRouter {
  return inject(routerKey)!!;
}
