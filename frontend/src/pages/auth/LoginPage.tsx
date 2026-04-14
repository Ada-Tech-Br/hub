import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Mail, ArrowRight } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";
import { getApiErrorMessage } from "@/lib/api";

const emailSchema = z.object({ email: z.string().email("E-mail inválido") });
const otpSchema = z.object({ code: z.string().length(6, "Código deve ter 6 dígitos") });

type EmailForm = z.infer<typeof emailSchema>;
type OtpForm = z.infer<typeof otpSchema>;

type Step = "email" | "otp";

export function LoginPage() {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/dashboard";

  const emailForm = useForm<EmailForm>({ resolver: zodResolver(emailSchema) });
  const otpForm = useForm<OtpForm>({ resolver: zodResolver(otpSchema) });

  async function handleEmailSubmit(data: EmailForm) {
    setIsLoading(true);
    try {
      await authService.requestOtp(data.email);
      setEmail(data.email);
      setStep("otp");
      toast.success("Código enviado para seu e-mail!");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleOtpSubmit(data: OtpForm) {
    setIsLoading(true);
    try {
      const result = await authService.verifyOtp(email, data.code);
      setAuth(result.user, result.access_token, result.refresh_token);
      toast.success(`Bem-vindo, ${result.user.name}!`);
      navigate(redirectTo, { replace: true });
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  function handleGoogleLogin() {
    window.location.href = authService.getGoogleLoginUrl();
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-ada-50 to-ada-100 p-4">
      <div className="w-full max-w-md animate-fade-in">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary shadow-lg">
            <span className="text-2xl font-bold text-primary-foreground">A</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Ada Platform</h1>
          <p className="mt-1 text-sm text-muted-foreground">Hub digital de projetos e arquivos</p>
        </div>

        <Card className="shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">
              {step === "email" ? "Entrar na plataforma" : "Verificar código"}
            </CardTitle>
            <CardDescription>
              {step === "email"
                ? "Use seu e-mail corporativo ou conta Google"
                : `Digite o código enviado para ${email}`}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {step === "email" && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  onClick={handleGoogleLogin}
                >
                  <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  Continuar com Google
                </Button>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <Separator />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-background px-2 text-muted-foreground">ou</span>
                  </div>
                </div>

                <form onSubmit={emailForm.handleSubmit(handleEmailSubmit)} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">E-mail</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="seu@email.com"
                      autoComplete="email"
                      {...emailForm.register("email")}
                    />
                    {emailForm.formState.errors.email && (
                      <p className="text-xs text-destructive">{emailForm.formState.errors.email.message}</p>
                    )}
                  </div>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Mail className="mr-2 h-4 w-4" />
                    )}
                    Receber código de acesso
                  </Button>
                </form>
              </>
            )}

            {step === "otp" && (
              <form onSubmit={otpForm.handleSubmit(handleOtpSubmit)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="code">Código de verificação</Label>
                  <Input
                    id="code"
                    type="text"
                    placeholder="000000"
                    maxLength={6}
                    autoComplete="one-time-code"
                    className="text-center text-2xl tracking-[0.5em] font-mono"
                    {...otpForm.register("code")}
                  />
                  {otpForm.formState.errors.code && (
                    <p className="text-xs text-destructive">{otpForm.formState.errors.code.message}</p>
                  )}
                </div>

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <ArrowRight className="mr-2 h-4 w-4" />
                  )}
                  Verificar e entrar
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  className="w-full"
                  onClick={() => {
                    setStep("email");
                    otpForm.reset();
                  }}
                >
                  Usar outro e-mail
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        <p className="mt-4 text-center text-xs text-muted-foreground">
          Ao entrar, você concorda com os termos de uso da plataforma Ada.
        </p>
      </div>
    </div>
  );
}
