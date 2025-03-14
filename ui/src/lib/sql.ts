import postgres from "postgres";

let __sql: postgres.Sql<{}>;

if (process.env.NODE_ENV === "production") {
  __sql = postgres(process.env!.POSTGRES_URL!);
} else {
  if (!(global as any).__sql) {
    (global as any).__sql = postgres(process.env!.POSTGRES_URL!);
  }

  __sql = (global as any).__sql;
}

export { __sql as sql };
